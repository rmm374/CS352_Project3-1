#!/usr/bin/env python3
"""
rudp_server_filled.py — Minimal Reliable UDP (RUDP) server (single-client, stop-and-wait).

Implements:
  1) 3-way handshake:  SYN -> (send) SYN-ACK -> (expect) ACK
  2) DATA handling: in-order DATA(seq=n) -> (send) DATA-ACK(seq=n); keep expect_seq
     - if out-of-order, re-ACK last in-order packet (expect_seq - 1)
  3) Teardown: (expect) FIN -> (send) FIN-ACK -> reset state
"""
import socket, struct

# ===================== CONFIG (EDIT YOUR PORT) =====================
ASSIGNED_PORT = 30077  # <-- replace with your assigned UDP port if needed
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

        # ============ PHASE 1: HANDSHAKE ============
        if not established:
            # Only accept packets from the first client that sends SYN
            if tp == SYN and client_addr is None:
                client_addr = addr
                print('[SERVER] got SYN from', addr)
                sock.sendto(pack_msg(SYN_ACK, 0), client_addr)
                continue
            # Complete handshake on ACK from the same client
            if tp == ACK and client_addr == addr:
                established = True
                expect_seq = 0
                print('[SERVER] handshake complete with', client_addr)
                continue
            # Ignore anything else while not established
            continue
        # ============================================

        # Ignore packets from other addresses once a client is set
        if client_addr is not None and addr != client_addr:
            # Silently ignore or print a note
            continue

        # ============ PHASE 2: DATA =================
        if tp == DATA:
            if seq == expect_seq:
                # "Deliver" payload (print as text)
                try:
                    text = pl.decode('utf-8', errors='replace')
                except Exception:
                    text = str(pl)
                print(f'[SERVER] DATA seq={seq} len={len(pl)}')
                if text:
                    print(text, end='')  # payload may already contain newlines
                # ACK the received seq and advance
                sock.sendto(pack_msg(DATA_ACK, seq), client_addr)
                expect_seq += 1
            else:
                # Out-of-order: re-ACK the last in-order seq (expect_seq - 1)
                last_in_order = expect_seq - 1 if expect_seq > 0 else 0
                print(f'[SERVER] out-of-order DATA seq={seq} (expect {expect_seq}); re-ACK {last_in_order}')
                sock.sendto(pack_msg(DATA_ACK, last_in_order), client_addr)
            continue
        # ============================================

        # ============ PHASE 3: TEARDOWN =============
        if tp == FIN:
            print('[SERVER] FIN received from', addr, '- closing')
            sock.sendto(pack_msg(FIN_ACK, 0), client_addr)
            # Reset state to allow a new client
            established = False
            client_addr = None
            expect_seq = 0
            print('[SERVER] connection reset; waiting for new client')
            continue
        # ============================================

        # Optional: ignore stray types (ACKs, etc.)

if __name__ == '__main__':
    main()
