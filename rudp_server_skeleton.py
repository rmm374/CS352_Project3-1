#!/usr/bin/env python3
"""
Minimal Reliable UDP (RUDP) server — single-client, stop-and-wait.
- Prints exact rubric messages
- Adds random 100–1000 ms delay before every DATA-ACK (incl. re-ACK)
"""
import socket, struct, time, random

# ===================== CONFIG (EDIT YOUR PORT) =====================
ASSIGNED_PORT = 30077  # your assigned UDP port
# ==================================================================

# --- Protocol type codes (1 byte) ---
SYN, SYN_ACK, ACK, DATA, DATA_ACK, FIN, FIN_ACK = 1, 2, 3, 4, 5, 6, 7

# Header format: type(1B) | seq(4B) | len(2B)
HDR = '!B I H'
HDR_SZ = struct.calcsize(HDR)

def pack_msg(tp: int, seq: int, payload: bytes = b'') -> bytes:
    if isinstance(payload, str):
        payload = payload.encode()
    return struct.pack(HDR, tp, seq, len(payload)) + payload

def unpack_msg(pkt: bytes):
    if len(pkt) < HDR_SZ:
        return None, None, b''
    tp, seq, ln = struct.unpack(HDR, pkt[:HDR_SZ])
    return tp, seq, pkt[HDR_SZ:HDR_SZ+ln]

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', ASSIGNED_PORT))
    print(f'[SERVER] Listening on 0.0.0.0:{ASSIGNED_PORT} (UDP)')

    client_addr = None
    established = False
    expect_seq = 0  # next in-order DATA seq we expect

    while True:
        pkt, addr = sock.recvfrom(2048)
        tp, seq, pl = unpack_msg(pkt)
        if tp is None:
            continue

        # ===== PHASE 1: HANDSHAKE =====
        if not established:
            # Only accept the first client that sends SYN
            if tp == SYN and client_addr is None:
                client_addr = addr
                print('[SERVER] got SYN from', addr)
                sock.sendto(pack_msg(SYN_ACK, 0), client_addr)
                continue
            if tp == ACK and addr == client_addr:
                established = True
                expect_seq = 0
                print('[SERVER] Connection established')  # exact wording
                continue
            # Ignore everything else until established
            continue
        # ==============================

        # Ignore packets from other senders once a client is set
        if client_addr is not None and addr != client_addr:
            continue

        # ===== PHASE 2: DATA =====
        if tp == DATA:
            # Random ACK delay BEFORE replying (required by spec)
            delay_ms = random.randint(100, 1000)
            time.sleep(delay_ms / 1000.0)

            if seq == expect_seq:
                # Deliver payload (print nicely)
                try:
                    text = pl.decode('utf-8', errors='replace')
                except Exception:
                    text = str(pl)
                print(f'[SERVER] DATA seq={seq} len={len(pl)} (delay={delay_ms}ms)')
                if text:
                    print(text, end='')
                # ACK this seq and advance window
                sock.sendto(pack_msg(DATA_ACK, seq), client_addr)
                expect_seq += 1
            else:
                # Out-of-order: re-ACK last in-order
                last_in_order = expect_seq - 1 if expect_seq > 0 else 0
                print(f'[SERVER] out-of-order DATA seq={seq} (expect {expect_seq}); '
                      f're-ACK {last_in_order} (delay={delay_ms}ms)')
                sock.sendto(pack_msg(DATA_ACK, last_in_order), client_addr)
            continue
        # =========================

        # ===== PHASE 3: TEARDOWN =====
        if tp == FIN:
            print('[SERVER] FIN received from', addr)
            sock.sendto(pack_msg(FIN_ACK, 0), client_addr)
            print('[SERVER] Connection closed')  # exact wording
            # Reset to accept a new client
            established = False
            client_addr = None
            expect_seq = 0
            continue
        # =============================

if __name__ == '__main__':
    main()
