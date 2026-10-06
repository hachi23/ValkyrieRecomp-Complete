#version 450
/* Textured fragment: sample raw 1555 VRAM (integer), CLUT-decode per depth,
 * texture window, optional bilinear, texel-0 cutout discard, STP-split discard,
 * PS1 *2-around-0x80 colour modulation. Output alpha = bit15 of the written
 * pixel. Ported verbatim from the GL backend's TEX_FS (usampler2D u_vram = the
 * native R16_UINT raw VRAM mirror). */
layout(location = 0) noperspective in vec2  v_uv;
layout(location = 1) noperspective in vec4  v_col;
layout(location = 2) flat in ivec2 v_tpage;   /* texture page base, VRAM px */
layout(location = 3) flat in ivec2 v_clut;    /* CLUT base, VRAM px */
layout(location = 4) flat in int   v_depth;   /* 0=4bit 1=8bit 2=15bit */
layout(location = 5) flat in int   v_raw;     /* 1 = no colour modulation */
layout(location = 6) flat in ivec4 v_limits;  /* prim uv bounds (inclusive) */
layout(location = 7) smooth in vec2 v_uv_p;   /* perspective-correct UV */
layout(location = 8) flat   in int  v_persp;  /* 1 = use v_uv_p, else affine */

layout(set = 0, binding = 0) uniform usampler2D u_vram;

layout(push_constant) uniform PC {
    float u_shift;
    float u_xoff;
    float u_xhalf;
    int   u_semipass;   /* 0=all texels, 1=STP=0 only, 2=STP=1 only */
    int   u_maskset;    /* GP0(E6h) set-mask: OR bit15 into output */
    int   u_filter;     /* bits 0-1: 0 nearest, 1 bilinear, 2 smooth; bit 2: de-dither */
    ivec4 u_twin;       /* texture window: mask_x, mask_y, off_x, off_y */
} pc;

layout(location = 0) out vec4 frag;

int vram_at(int x, int y) {
    return int(texelFetch(u_vram, ivec2(x & 1023, y & 511), 0).r);
}
int fetch_texel(int u, int v) {
    u &= 255; v &= 255;
    if ((pc.u_twin.x | pc.u_twin.y) != 0) {
        u = (u & ~(pc.u_twin.x * 8)) | ((pc.u_twin.z & pc.u_twin.x) * 8);
        v = (v & ~(pc.u_twin.y * 8)) | ((pc.u_twin.w & pc.u_twin.y) * 8);
    } else {
        u = clamp(u, v_limits.x, v_limits.z);
        v = clamp(v, v_limits.y, v_limits.w);
    }
    if (v_depth == 0) {
        int px = vram_at(v_tpage.x + (u >> 2), v_tpage.y + v);
        return vram_at(v_clut.x + ((px >> ((u & 3) * 4)) & 0xF), v_clut.y);
    } else if (v_depth == 1) {
        int px = vram_at(v_tpage.x + (u >> 1), v_tpage.y + v);
        return vram_at(v_clut.x + ((px >> ((u & 1) * 8)) & 0xFF), v_clut.y);
    }
    return vram_at(v_tpage.x + u, v_tpage.y + v);
}
vec3 col5(int raw) {
    return vec3(float(raw & 31), float((raw >> 5) & 31), float((raw >> 10) & 31)) / 31.0;
}
/* Perceptual distance between two 15-bit colours (xBR's YUV weighting). */
float cdist(int a, int b) {
    vec3 d = col5(a) - col5(b);
    float y = abs(0.299 * d.r + 0.587 * d.g + 0.114 * d.b);
    float u = abs(-0.169 * d.r - 0.331 * d.g + 0.500 * d.b);
    float v = abs(0.500 * d.r - 0.419 * d.g - 0.081 * d.b);
    return 48.0 * y + 7.0 * u + 6.0 * v;
}
/* Dither and painted gradients differ by a few 5-bit steps; only edges
 * stronger than that count, so smoothing never redraws texture noise. */
bool same(int a, int b) { return cdist(a, b) < 3.0; }

/* Colour of texel (u,v) with a two-colour checkerboard blended away: when the
 * four orthogonal neighbours agree with each other and differ only slightly
 * from the centre, the centre is half of an ordered dither. */
vec3 dedithered(int u, int v, int c) {
    int n = fetch_texel(u, v - 1), s = fetch_texel(u, v + 1);
    int w = fetch_texel(u - 1, v), e = fetch_texel(u + 1, v);
    if (n == 0 || s == 0 || w == 0 || e == 0) return col5(c);
    bool ring = cdist(n, s) < 1.2 && cdist(w, e) < 1.2 && cdist(n, w) < 2.0;
    float dc = cdist(c, n);
    if (!ring || dc < 0.05 || dc > 4.0) return col5(c);
    return mix(col5(c), (col5(n) + col5(s) + col5(w) + col5(e)) * 0.25, 0.5);
}

/* xBR level-1 corner test in texel space. (dx,dy) points at the corner of
 * texel E nearest the fragment; returns the texel to blend toward, or -1. */
int xbr_corner(int iu, int iv, int dx, int dy, int e) {
    int f = fetch_texel(iu + dx, iv), h = fetch_texel(iu, iv + dy);
    if (same(e, f) || same(e, h)) return -1;
    int i  = fetch_texel(iu + dx, iv + dy);
    int d  = fetch_texel(iu - dx, iv), b = fetch_texel(iu, iv - dy);
    int c  = fetch_texel(iu + dx, iv - dy), g = fetch_texel(iu - dx, iv + dy);
    int f4 = fetch_texel(iu + 2 * dx, iv), h5 = fetch_texel(iu, iv + 2 * dy);
    int i4 = fetch_texel(iu + 2 * dx, iv + dy), i5 = fetch_texel(iu + dx, iv + 2 * dy);
    float across = cdist(e, c) + cdist(e, g) + cdist(i, f4) + cdist(i, h5) + 4.0 * cdist(h, f);
    float along  = cdist(h, d) + cdist(h, i5) + cdist(f, i4) + cdist(f, b) + 4.0 * cdist(e, i);
    if (across >= along) return -1;
    return cdist(e, f) <= cdist(e, h) ? f : h;
}

void main() {
    int stp; vec3 rgb;
    /* v_persp is 0 for every prim unless [video] perspective_texturing is on
     * AND this prim's packet carried full GTE projection provenance, so the
     * default is the PS1's affine (noperspective) mapping. */
    vec2 uv = (v_persp != 0) ? v_uv_p : v_uv;
    int mode = pc.u_filter & 3;
    bool dedither = (pc.u_filter & 4) != 0;
    if (mode == 0) {
        int iu = int(floor(uv.x)), iv = int(floor(uv.y));
        int raw = fetch_texel(iu, iv);
        if (raw == 0) discard;
        rgb = dedither ? dedithered(iu, iv, raw) : col5(raw);
        stp = (raw >> 15) & 1;
    } else if (mode == 2) {
        int iu = int(floor(uv.x)), iv = int(floor(uv.y));
        int e = fetch_texel(iu, iv);
        if (e == 0) discard;
        float fx = uv.x - float(iu), fy = uv.y - float(iv);
        int dx = fx >= 0.5 ? 1 : -1, dy = fy >= 0.5 ? 1 : -1;
        rgb = dedither ? dedithered(iu, iv, e) : col5(e);
        stp = (e >> 15) & 1;
        int target = xbr_corner(iu, iv, dx, dy, e);
        if (target >= 0) {
            /* Distance past the corner's diagonal, 0 at the line, ~1 at the
             * corner itself; a short ramp keeps the new edge antialiased
             * without blurring the flat areas either side of it. */
            float px = dx > 0 ? fx : 1.0 - fx, py = dy > 0 ? fy : 1.0 - fy;
            float cover = smoothstep(1.45, 1.55, px + py);
            if (target == 0) {
                if (cover > 0.5) discard;
            } else {
                rgb = mix(rgb, col5(target), cover);
            }
        }
    } else {
        /* Bilinear, Beetle-PSX formulation: the NEAREST texel is the base
         * (cutout + STP authority), the neighbours lie toward the sub-texel
         * offset and clamp to v_limits. Transparent neighbours are ignored and
         * the colour is renormalised, but a transparent base stays cut out.
         * v_uv is aligned for PS1 top-left point sampling; recenter the
         * bilinear footprint so 1x rect tiles sample their own texels. */
        uv += vec2(pc.u_shift);
        int iu = int(floor(uv.x)), iv = int(floor(uv.y));
        float fx = uv.x - float(iu) - 0.5, fy = uv.y - float(iv) - 0.5;
        int sx = fx < 0.0 ? -1 : 1, sy = fy < 0.0 ? -1 : 1;
        fx = abs(fx); fy = abs(fy);
        int c00 = fetch_texel(iu, iv);
        if (c00 == 0) discard;
        int c10 = fetch_texel(iu + sx, iv);
        int c01 = fetch_texel(iu, iv + sy);
        int c11 = fetch_texel(iu + sx, iv + sy);
        float w00 = (c00 == 0 ? 0.0 : 1.0) * (1.0 - fx) * (1.0 - fy);
        float w10 = (c10 == 0 ? 0.0 : 1.0) * fx * (1.0 - fy);
        float w01 = (c01 == 0 ? 0.0 : 1.0) * (1.0 - fx) * fy;
        float w11 = (c11 == 0 ? 0.0 : 1.0) * fx * fy;
        float opac = w00 + w10 + w01 + w11;
        rgb = (col5(c00) * w00 + col5(c10) * w10 + col5(c01) * w01 + col5(c11) * w11) / opac;
        float stpf = (float((c00 >> 15) & 1) * w00 + float((c10 >> 15) & 1) * w10
                    + float((c01 >> 15) & 1) * w01 + float((c11 >> 15) & 1) * w11) / opac;
        stp = stpf >= 0.5 ? 1 : 0;
    }
    if (pc.u_semipass == 1 && stp == 1) discard;
    if (pc.u_semipass == 2 && stp == 0) discard;
    if (v_raw == 0) rgb = clamp(rgb * v_col.rgb * 2.0, 0.0, 1.0);
    frag = vec4(rgb, (stp == 1 || pc.u_maskset == 1) ? 1.0 : 0.0);
}
