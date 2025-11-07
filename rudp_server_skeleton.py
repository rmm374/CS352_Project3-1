#!/usr/bin/env python3
"""
rudp_server_skeleton.py — STUDENT SKELETON
Goal: Implement a minimal "Reliable UDP" (RUDP) server over UDP.

YOU MUST IMPLEMENT:
  1) 3-way handshake:  SYN -> (you send) SYN-ACK -> (expect) ACK
  2) DATA handling with sequence numbers + send DATA-ACK for each in-order DATA
     - maintain 'expect_seq' (next in-order sequence number you expect)
     - if out-of-order, re-ACK the last in-order seq (expect_seq - 1)
  3) Teardown: (expect) FIN -> (you send) FIN-ACK

Tips:
  - Use Wireshark with filter: udp.port == <your_assigned_port>
  - Keep the server single-client and single-threaded for simplicity.
  - Only accept packets from the first client after handshake begins.
"""
import socket, struct

# ===================== CONFIG (EDIT YOUR PORT) =====================
ASSIGNED_PORT = 30077  # <-- REPLACE with your assigned UDP port
# ==================================================================

# --- Protocol type codes (1 byte) ---
SYN, SYN_ACK, ACK, DATA, DATA_ACK, FIN, FIN_ACK = 1,2,3,4,5,6,7

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

        # ============ PHASE 1: HANDSHAKE (YOU IMPLEMENT) ============
        if not established:
            # TODO:
            #  - If this is a SYN and we are not established:
            #       * set client_addr = addr
            #       * print('[SERVER] got SYN from', addr)
            #       * send SYN-ACK to client_addr
            #       * continue
            #  - If this is the final ACK from the same client:
            #       * print('[SERVER] handshake complete')
            #       * established = True; expect_seq = 0
            #       * continue
            #  - Ignore packets from others until established
            # HINT: Only accept packets from the first client that sent SYN
            pass  # <-- replace with your handshake logic
            continue
        # ============================================================

        # Ignore packets from other addresses once a client is set
        if client_addr is not None and addr != client_addr:
            # Optional: silently ignore or print a message
            continue

        # ============ PHASE 2: DATA (YOU IMPLEMENT) =================
        if tp == DATA:
            # TODO:
            #   - If seq == expect_seq:
            #       * "deliver" the payload (e.g., print it as text)
            #       * send DATA-ACK with the same seq
            #       * expect_seq += 1
            #   - Else (out-of-order):
            #       * re-ACK the last in-order packet (expect_seq - 1)
            pass  # <-- replace with your data logic
            continue
        # ============================================================

        # ============ PHASE 3: TEARDOWN (YOU IMPLEMENT) =============
        if tp == FIN:
            # TODO:
            #   - print('[SERVER] FIN received, closing')
            #   - send FIN-ACK to client_addr
            #   - reset state: established=False; client_addr=None; expect_seq=0
            pass  # <-- replace with your teardown logic
            continue
        # ============================================================

if __name__ == '__main__':
    main()
