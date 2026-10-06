#include "ra_host.h"

#include <cstdio>
#include <cstring>

#if !defined(PSX_HAVE_RCHEEVOS)

int  ra_available(void) { return 0; }
void ra_start(const char *, const char *, int, const char *) {}
int  ra_login_password(const char *, const char *, char *, size_t, char *msg, size_t cap) {
    if (msg && cap) std::snprintf(msg, cap, "This build has no RetroAchievements support.");
    return 0;
}
void ra_change_disc(const char *) {}
void ra_on_vblank(void) {}
int  ra_hardcore_active(void) { return 0; }
void ra_status(char *out, size_t cap) { if (out && cap) std::snprintf(out, cap, "unavailable"); }
void ra_shutdown(void) {}

#else

#include "host_osd.h"
#include "session_log.h"

#include <rc_client.h>
#include <rc_consoles.h>
#include <rc_hash.h>
#include <curl/curl.h>

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <mutex>
#include <string>
#include <thread>

extern "C" uint8_t *g_psx_ram;
extern "C" uint8_t  psx_read_byte(uint32_t addr);

namespace {

constexpr uint32_t kRamBytes = 0x200000u;
constexpr uint32_t kScratchBase = 0x200000u;  /* RetroAchievements' PS1 map */
constexpr uint32_t kScratchBytes = 0x400u;

rc_client_t *g_client;
std::atomic<int> g_hardcore_requested{0};
std::atomic<int> g_game_loaded{0};
std::string g_disc_path;
std::mutex g_toast_mutex;
std::deque<std::string> g_toasts;

void toast(const std::string &text) {
    std::lock_guard<std::mutex> lock(g_toast_mutex);
    g_toasts.push_back(text);
}

uint32_t read_memory(uint32_t address, uint8_t *buffer, uint32_t num_bytes, rc_client_t *) {
    uint32_t done = 0;
    for (; done < num_bytes; ++done) {
        const uint32_t a = address + done;
        if (a < kRamBytes) buffer[done] = g_psx_ram[a];
        else if (a - kScratchBase < kScratchBytes) buffer[done] = psx_read_byte(0x1F800000u + (a - kScratchBase));
        else break;
    }
    return done;
}

size_t collect(char *data, size_t size, size_t count, void *out) {
    static_cast<std::string *>(out)->append(data, size * count);
    return size * count;
}

void server_call(const rc_api_request_t *request, rc_client_server_callback_t callback,
                 void *callback_data, rc_client_t *client) {
    std::string url = request->url;
    std::string post = request->post_data ? request->post_data : "";
    std::string type = request->content_type ? request->content_type : "";
    /* `request` is freed when this function returns; the thread uses copies. */
    const bool has_post = request->post_data != nullptr;
    char clause[128] = "";
    rc_client_get_user_agent_clause(client, clause, sizeof clause);
    std::string agent = std::string("ValkyrieRecomp/1.0 ") + clause;
    std::thread([=]() {
        std::string body;
        long status = RC_API_SERVER_RESPONSE_CLIENT_ERROR;
        if (CURL *curl = curl_easy_init()) {
            curl_slist *headers = nullptr;
            if (!type.empty()) headers = curl_slist_append(headers, ("Content-Type: " + type).c_str());
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_USERAGENT, agent.c_str());
            curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
            curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);
            /* The MinGW libcurl ships no CA bundle; without this every HTTPS
             * request fails with CURLE_SSL_CACERT_BADFILE. */
            curl_easy_setopt(curl, CURLOPT_SSL_OPTIONS, static_cast<long>(CURLSSLOPT_NATIVE_CA));
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, collect);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &body);
            if (headers) curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            if (has_post) curl_easy_setopt(curl, CURLOPT_COPYPOSTFIELDS, post.c_str());
            const CURLcode rc = curl_easy_perform(curl);
            if (rc == CURLE_OK)
                curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &status);
            else
                session_log_event("retroachievements: request failed (%s)", curl_easy_strerror(rc));
            curl_slist_free_all(headers);
            curl_easy_cleanup(curl);
        }
        rc_api_server_response_t response{body.c_str(), body.size(), static_cast<int>(status)};
        callback(&response, callback_data);
    }).detach();
}

void log_message(const char *message, const rc_client_t *) {
    std::fprintf(stdout, "psxrecomp: ra: %s\n", message);
}

void on_event(const rc_client_event_t *event, rc_client_t *) {
    switch (event->type) {
    case RC_CLIENT_EVENT_ACHIEVEMENT_TRIGGERED:
        toast(std::string("Achievement unlocked: ") + event->achievement->title + " (" +
              std::to_string(event->achievement->points) + ")");
        session_log_event("achievement unlocked: %s", event->achievement->title);
        break;
    case RC_CLIENT_EVENT_GAME_COMPLETED:
        toast("All achievements earned!");
        break;
    case RC_CLIENT_EVENT_SERVER_ERROR:
        toast("RetroAchievements error: " + std::string(event->server_error->error_message));
        break;
    case RC_CLIENT_EVENT_DISCONNECTED:
        toast("RetroAchievements: offline, unlocks will be sent later");
        break;
    case RC_CLIENT_EVENT_RECONNECTED:
        toast("RetroAchievements: back online, pending unlocks sent");
        break;
    default:
        break;
    }
}

void on_game_loaded(int result, const char *error, rc_client_t *client, void *) {
    if (result != RC_OK) {
        toast(std::string("RetroAchievements: ") + (error ? error : "game not loaded"));
        session_log_event("retroachievements: game not loaded (%s)", error ? error : "?");
        return;
    }
    g_game_loaded = 1;
    rc_client_user_game_summary_t summary{};
    rc_client_get_user_game_summary(client, &summary);
    const rc_client_game_t *game = rc_client_get_game_info(client);
    char text[160];
    std::snprintf(text, sizeof text, "%s: %u of %u achievements%s", game ? game->title : "Game",
                  summary.num_unlocked_achievements, summary.num_core_achievements,
                  rc_client_get_hardcore_enabled(client) ? " (hardcore)" : "");
    toast(text);
    session_log_event("retroachievements: game %u loaded, %s", game ? game->id : 0, text);
}

void on_login(int result, const char *error, rc_client_t *client, void *) {
    if (result != RC_OK) {
        toast(std::string("RetroAchievements login failed: ") + (error ? error : "?"));
        session_log_event("retroachievements: login failed (%s)", error ? error : "?");
        return;
    }
    const rc_client_user_t *user = rc_client_get_user_info(client);
    session_log_event("retroachievements: logged in as %s", user ? user->display_name : "?");
    rc_client_begin_identify_and_load_game(client, RC_CONSOLE_PLAYSTATION, g_disc_path.c_str(),
                                           nullptr, 0, on_game_loaded, nullptr);
}

void on_disc_changed(int result, const char *error, rc_client_t *, void *) {
    if (result == RC_OK) {
        session_log_event("retroachievements: disc change accepted");
        return;
    }
    toast(std::string("RetroAchievements: ") + (error ? error : "disc not recognised"));
    session_log_event("retroachievements: disc change failed (%s)", error ? error : "?");
}

rc_client_t *make_client(void) {
    static std::once_flag once;
    std::call_once(once, [] {
        curl_global_init(CURL_GLOBAL_DEFAULT);
        rc_hash_init_default_cdreader();
    });
    rc_client_t *client = rc_client_create(read_memory, server_call);
    if (!client) return nullptr;
    rc_client_enable_logging(client, RC_CLIENT_LOG_LEVEL_WARN, log_message);
    rc_client_set_allow_background_memory_reads(client, 0);
    rc_client_set_event_handler(client, on_event);
    return client;
}

}  // namespace

int ra_available(void) { return 1; }

void ra_start(const char *username, const char *token, int hardcore, const char *disc_path) {
    if (g_client || !username || !*username || !token || !*token || !disc_path) return;
    g_client = make_client();
    if (!g_client) return;
    g_disc_path = disc_path;
    g_hardcore_requested = hardcore ? 1 : 0;
    rc_client_set_hardcore_enabled(g_client, hardcore ? 1 : 0);
    rc_client_begin_login_with_token(g_client, username, token, on_login, nullptr);
}

void ra_change_disc(const char *disc_path) {
    /* Before the set loads, every disc of the game identifies the same set. */
    if (!g_client || !disc_path || !g_game_loaded) return;
    rc_client_begin_identify_and_change_media(g_client, disc_path, nullptr, 0,
                                              on_disc_changed, nullptr);
}

int ra_login_password(const char *username, const char *password, char *token_out,
                      size_t token_cap, char *msg, size_t msg_cap) {
    rc_client_t *client = make_client();
    if (!client) {
        std::snprintf(msg, msg_cap, "Could not start RetroAchievements.");
        return 0;
    }
    struct Wait {
        std::mutex m;
        std::condition_variable cv;
        bool done = false;
        int result = 0;
        std::string error;
    };
    auto *wait = new Wait();
    rc_client_begin_login_with_password(client, username, password,
        [](int result, const char *error, rc_client_t *, void *data) {
            auto *w = static_cast<Wait *>(data);
            std::lock_guard<std::mutex> lock(w->m);
            w->result = result;
            w->error = error ? error : "";
            w->done = true;
            w->cv.notify_all();
        }, wait);
    int ok = 0;
    bool answered;
    {
        std::unique_lock<std::mutex> lock(wait->m);
        answered = wait->cv.wait_for(lock, std::chrono::seconds(20), [&] { return wait->done; });
        if (!answered) {
            std::snprintf(msg, msg_cap, "RetroAchievements did not answer. Check your connection.");
        } else if (wait->result != RC_OK) {
            std::snprintf(msg, msg_cap, "Login failed: %s", wait->error.c_str());
        } else {
            const rc_client_user_t *user = rc_client_get_user_info(client);
            std::snprintf(token_out, token_cap, "%s", user && user->token ? user->token : "");
            std::snprintf(msg, msg_cap, "Logged in as %s.", user ? user->display_name : username);
            ok = token_out[0] != '\0';
        }
    }
    /* A timed-out request can still call back later: leave that client and
     * its wait state alive instead of racing the late callback. */
    if (answered) {
        rc_client_destroy(client);
        delete wait;
    }
    return ok;
}

void ra_on_vblank(void) {
    if (!g_client) return;
    rc_client_do_frame(g_client);
    std::deque<std::string> pending;
    {
        std::lock_guard<std::mutex> lock(g_toast_mutex);
        pending.swap(g_toasts);
    }
    for (const auto &text : pending) host_osd_push(text.c_str(), 4000);
}

int ra_hardcore_active(void) {
    return g_client && g_hardcore_requested && rc_client_get_hardcore_enabled(g_client) ? 1 : 0;
}

void ra_status(char *out, size_t cap) {
    if (!out || !cap) return;
    if (!g_client) { std::snprintf(out, cap, "off"); return; }
    const rc_client_user_t *user = rc_client_get_user_info(g_client);
    const rc_client_game_t *game = rc_client_get_game_info(g_client);
    rc_client_user_game_summary_t summary{};
    if (g_game_loaded) rc_client_get_user_game_summary(g_client, &summary);
    std::snprintf(out, cap, "user=%s game=%u loaded=%d hardcore=%d unlocked=%u/%u",
                  user ? user->display_name : "-", game ? game->id : 0, g_game_loaded.load(),
                  ra_hardcore_active(), summary.num_unlocked_achievements,
                  summary.num_core_achievements);
}

void ra_shutdown(void) {
    if (!g_client) return;
    rc_client_destroy(g_client);
    g_client = nullptr;
}

#endif
