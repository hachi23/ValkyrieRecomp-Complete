#!/usr/bin/env python3
"""Replay a verified local checkpoint through the native debug protocol."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import signal
import struct
import subprocess
import sys
import tempfile
import time
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'psxrecomp/tools'))
from debug_client import query


@dataclass(frozen=True)
class Checkpoint:
    name: str
    slot: int | None
    path: Path | None
    disc: int
    verification: str | None


@dataclass(frozen=True)
class InputSpan:
    frames: int
    buttons: int


@dataclass(frozen=True)
class Scenario:
    name: str
    checkpoint: Checkpoint
    inputs: tuple[InputSpan, ...]
    capture: str


def require_fields(value, expected, context):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f'{context} requires exactly {", ".join(expected)}')
    return value


def integer(value, low, high, context):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{context} must be an integer between {low} and {high}')
    return value


def validate_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', value):
        raise ValueError(f'invalid name {value!r}')
    return value


def load_manifest(path):
    raw = require_fields(json.loads(path.read_text()), ('checkpoints', 'scenarios'), 'manifest')
    if not isinstance(raw['checkpoints'], dict) or not isinstance(raw['scenarios'], dict):
        raise ValueError('checkpoints and scenarios must be objects')
    checkpoints = {}
    for key, value in raw['checkpoints'].items():
        validate_name(key)
        require_fields(value, ('slot', 'path', 'disc', 'verification'), key)
        disc = integer(value['disc'], 1, 2, f'{key}.disc')
        slot, local_path, verification = value['slot'], value['path'], value['verification']
        if slot is None:
            if local_path is not None or verification is not None:
                raise ValueError(f'{key} must leave slot, path, and verification null together')
            checkpoints[key] = Checkpoint(key, None, None, disc, None)
            continue
        integer(slot, 0, 11, f'{key}.slot')
        if not isinstance(local_path, str) or not isinstance(verification, str) or not verification.strip():
            raise ValueError(f'{key} requires a local path and verification description')
        resolved = (ROOT / local_path).resolve()
        if Path(local_path).is_absolute() or not resolved.is_relative_to(ROOT / 'saves'):
            raise ValueError(f'{key}.path must remain inside the project saves directory')
        checkpoints[key] = Checkpoint(key, slot, resolved, disc, verification)
    scenarios = {}
    for key, value in raw['scenarios'].items():
        validate_name(key)
        require_fields(value, ('checkpoint', 'input', 'capture'), key)
        validate_name(value['checkpoint'])
        if value['checkpoint'] not in checkpoints:
            raise ValueError(f'{key} references an unknown checkpoint')
        spans = value['input']
        if not isinstance(spans, list) or not 1 <= len(spans) <= 4096:
            raise ValueError(f'{key}.input requires 1 to 4096 spans')
        inputs = []
        for span in spans:
            require_fields(span, ('frames', 'buttons'), f'{key}.input')
            inputs.append(InputSpan(integer(span['frames'], 1, 2147483647, 'frames'),
                                    integer(span['buttons'], 0, 65535, 'buttons')))
        capture = value['capture']
        if not isinstance(capture, str) or not re.fullmatch(r'[a-z][a-z0-9_]*\.png', capture):
            raise ValueError(f'{key}.capture requires a simple PNG filename')
        if inputs[-1].buttons != 65535:
            raise ValueError(f'{key} must end with neutral input, buttons 65535')
        scenarios[key] = Scenario(key, checkpoints[value['checkpoint']], tuple(inputs), capture)
    return checkpoints, scenarios


def require_checkpoint(checkpoint):
    if checkpoint.slot is None:
        raise ValueError(f'{checkpoint.name} has no recorded checkpoint; create and verify a real save before replay')
    if not checkpoint.path.is_file():
        raise ValueError(f'{checkpoint.name} save is missing at {checkpoint.path}')


def validate_png(path, response):
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('capture has no PNG signature')
    offset, dimensions, compressed, ended = 8, None, bytearray(), False
    while offset < len(data):
        if len(data) - offset < 12:
            raise ValueError('capture has a truncated PNG chunk')
        length = struct.unpack_from('>I', data, offset)[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError('capture has a truncated PNG payload')
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:end - 4]
        crc = struct.unpack_from('>I', data, end - 4)[0]
        if zlib.crc32(kind + payload) != crc:
            raise ValueError('capture has a corrupt PNG chunk')
        if dimensions is None:
            if kind != b'IHDR' or length != 13:
                raise ValueError('capture has no valid PNG header')
            dimensions = struct.unpack_from('>II', payload)
        if kind == b'IDAT':
            compressed.extend(payload)
        if kind == b'IEND':
            if length or end != len(data):
                raise ValueError('capture has an invalid PNG ending')
            ended = True
        offset = end
    if not ended or not compressed or dimensions != (response['width'], response['height']):
        raise ValueError('capture is incomplete or its dimensions disagree with the runtime')
    if not zlib.decompress(compressed):
        raise ValueError('capture has no pixel data')
    return {'width': dimensions[0], 'height': dimensions[1],
            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def run(scenario, host, port, timeout):
    require_checkpoint(scenario.checkpoint)
    output_root = ROOT / 'analysis/agent'
    ignored = subprocess.run(['git', 'check-ignore', '-q', str(output_root / 'probe')], cwd=ROOT)
    if ignored.returncode != 0:
        raise ValueError('analysis/agent outputs must be ignored by Git')
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output = Path(tempfile.mkdtemp(prefix=f'{stamp}_{scenario.name}_', dir=output_root))
    evidence = {'scenario': scenario.name, 'status': 'failed', 'host': host, 'port': port,
                'checkpoint': {'name': scenario.checkpoint.name, 'slot': scenario.checkpoint.slot,
                               'path': str(scenario.checkpoint.path), 'disc_expected': scenario.checkpoint.disc,
                               'verification': scenario.checkpoint.verification,
                               'sha256': hashlib.sha256(scenario.checkpoint.path.read_bytes()).hexdigest()},
                'commands': [], 'observations_required': [
                    'Inspect the captured scene; a valid PNG does not prove visual correctness.',
                    'Confirm the runtime launch uses the expected disc and save directory.',
                    'Gameplay, voice timing, complete FMV audio, memory-card restart, and Disc 2 remain unverified.',
                    'Capture occurs during live execution and is not aligned to an exact guest frame.']}

    def command(cmd, **kwargs):
        request = {'cmd': cmd, **kwargs}
        record = {'request': request}
        evidence['commands'].append(record)
        try:
            response = query(host, port, request)
            record['response'] = response
        except Exception as error:
            record['error'] = str(error)
            raise
        if not isinstance(response, dict) or response.get('ok') is not True:
            raise RuntimeError(f'{cmd} failed: {response}')
        return response

    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'received signal {signum}')

    previous = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGINT, signal.SIGTERM)}
    failure = None
    try:
        command('clear_input')
        initial = command('savestate_status')
        if initial['pending']:
            raise RuntimeError('runtime already has a pending save operation')
        command('savestate', op='load', slot=scenario.checkpoint.slot)
        deadline = time.monotonic() + timeout
        while True:
            receipt = command('savestate_status')
            if receipt['generation'] != initial['generation']:
                if (receipt['generation'] != (initial['generation'] + 1) % (1 << 32)
                        or receipt['pending'] != 0 or receipt['last_ok'] != 1
                        or receipt['last_op'] != 'load' or receipt['last_slot'] != scenario.checkpoint.slot):
                    raise RuntimeError(f'load completion failed or another client intervened: {receipt}')
                evidence['load_receipt'] = receipt
                break
            if time.monotonic() >= deadline:
                raise TimeoutError('timed out waiting for the load completion receipt')
            time.sleep(0.05)
        command('input_route_clear')
        for span in scenario.inputs:
            command('input_route_append', frames=span.frames, buttons=span.buttons)
        evidence['route_start'] = command('input_route_start')
        deadline = time.monotonic() + timeout
        while True:
            route = command('input_route_status')
            if not route['active']:
                if route['steps'] != len(scenario.inputs) or route['index'] != route['steps']:
                    raise RuntimeError(f'input route stopped before completion: {route}')
                evidence['route_receipt'] = route
                break
            if time.monotonic() >= deadline:
                raise TimeoutError('timed out waiting for input route completion')
            time.sleep(0.05)
        command('clear_input')
        evidence['frame_before_capture'] = command('frame')
        capture = output / scenario.capture
        response = command('screenshot_hires', path=str(capture))
        evidence['capture'] = {**validate_png(capture, response), 'path': str(capture), 'scale': response['scale']}
        evidence['frame_after_capture'] = command('frame')
        evidence['status'] = 'replay_completed_visual_review_required'
    except (Exception, KeyboardInterrupt) as error:
        failure = error
        evidence['error'] = str(error) or type(error).__name__
    finally:
        for sig in previous:
            signal.signal(sig, signal.SIG_IGN)
        try:
            command('clear_input')
            evidence['cleanup'] = 'clear_input acknowledged'
        except Exception as error:
            evidence['cleanup_error'] = str(error)
            evidence['status'] = 'failed'
            if failure is None:
                failure = error
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
        (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(output)
    if failure is not None:
        raise RuntimeError(evidence.get('error', evidence.get('cleanup_error'))) from failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_name('scenarios.json'))
    actions = parser.add_subparsers(dest='action', required=True)
    actions.add_parser('list')
    replay = actions.add_parser('run')
    replay.add_argument('scenario')
    replay.add_argument('--host', default='127.0.0.1')
    replay.add_argument('--port', type=int, default=4370)
    replay.add_argument('--timeout', type=float, default=30)
    args = parser.parse_args()
    try:
        checkpoints, scenarios = load_manifest(args.manifest)
        if args.action == 'list':
            for checkpoint in checkpoints.values():
                state = 'unrecorded' if checkpoint.slot is None else 'present' if checkpoint.path.is_file() else 'missing'
                print(f'checkpoint {checkpoint.name}: {state}')
            for scenario in scenarios.values():
                print(f'scenario {scenario.name}: checkpoint {scenario.checkpoint.name}')
            return 0
        if args.scenario not in scenarios:
            raise ValueError(f'unknown scenario {args.scenario!r}; use list')
        if not 1 <= args.port <= 65535 or not 0 < args.timeout <= 3600:
            raise ValueError('port must be 1 to 65535 and timeout must be greater than 0 and at most 3600 seconds')
        run(scenarios[args.scenario], args.host, args.port, args.timeout)
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f'error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
