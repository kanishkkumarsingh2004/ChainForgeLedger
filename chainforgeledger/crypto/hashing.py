"""
ChainForgeLedger Hashing Module

SHA-256 hashing implementation.
"""
import random
from typing import Union

p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
a = 0
b = 7

G = (
    0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
    0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
)

n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def right_rotate(x, n):
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF

def sha256_hash(message: Union[str, bytes]) -> str:
    """
    Calculate SHA-256 hash of the given message.
    
    Args:
        message: Input message as string or bytes
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    # Handle bytes input
    if isinstance(message, bytes):
        message_bytes = bytearray(message)
    elif isinstance(message, str):
        message_bytes = bytearray(message, 'utf-8')
    elif isinstance(message, bytearray):
        message_bytes = message
    else:
        raise TypeError("Message must be str, bytes, or bytearray")
    
    # Initial hash values (first 32 bits of the fractional parts of the square roots of the first 8 primes)
    h = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    ]

    # Round constants (first 32 bits of fractional parts of cube roots of first 64 primes)
    k = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
        0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
        0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
        0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
        0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
        0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
        0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
        0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ]

    # Pre-processing
    message = bytearray(message, 'utf-8')
    bit_length = len(message) * 8

    message.append(0x80)

    while (len(message) * 8) % 512 != 448:
        message.append(0)

    message += bit_length.to_bytes(8, 'big')

    # Process 512-bit chunks
    for chunk_start in range(0, len(message), 64):
        chunk = message[chunk_start:chunk_start + 64]
        w = [0] * 64

        for i in range(16):
            w[i] = int.from_bytes(chunk[i*4:(i*4)+4], 'big')

        for i in range(16, 64):
            s0 = right_rotate(w[i-15], 7) ^ right_rotate(w[i-15], 18) ^ (w[i-15] >> 3)
            s1 = right_rotate(w[i-2], 17) ^ right_rotate(w[i-2], 19) ^ (w[i-2] >> 10)
            w[i] = (w[i-16] + s0 + w[i-7] + s1) & 0xFFFFFFFF

        a, b, c, d, e, f, g, h_temp = h

        for i in range(64):
            S1 = right_rotate(e, 6) ^ right_rotate(e, 11) ^ right_rotate(e, 25)
            ch = (e & f) ^ (~e & g)
            temp1 = (h_temp + S1 + ch + k[i] + w[i]) & 0xFFFFFFFF
            S0 = right_rotate(a, 2) ^ right_rotate(a, 13) ^ right_rotate(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xFFFFFFFF

            h_temp = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        h = [
            (h[0] + a) & 0xFFFFFFFF,
            (h[1] + b) & 0xFFFFFFFF,
            (h[2] + c) & 0xFFFFFFFF,
            (h[3] + d) & 0xFFFFFFFF,
            (h[4] + e) & 0xFFFFFFFF,
            (h[5] + f) & 0xFFFFFFFF,
            (h[6] + g) & 0xFFFFFFFF,
            (h[7] + h_temp) & 0xFFFFFFFF
        ]

    return ''.join(f'{value:08x}' for value in h)


def sha256_hash_bytes(message: Union[str, bytes]) -> bytes:
    """
    Calculate SHA-256 hash of the given message and return as bytes.
    
    Args:
        message: Input message as string or bytes
        
    Returns:
        SHA-256 hash as bytes
    """
    hex_hash = sha256_hash(message)
    return bytes.fromhex(hex_hash)


# Rotation offsets
ROTATION_OFFSETS = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]

# Round constants
ROUND_CONSTANTS = [
    0x0000000000000001, 0x0000000000008082,
    0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088,
    0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B,
    0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080,
    0x0000000080000001, 0x8000000080008008,
]

def rotl(x, n):
    return ((x << n) | (x >> (64 - n))) & 0xFFFFFFFFFFFFFFFF

def keccak_f(state):
    for rc in ROUND_CONSTANTS:
        # Theta
        C = [state[x] ^ state[x+5] ^ state[x+10] ^ state[x+15] ^ state[x+20] for x in range(5)]
        D = [C[(x-1)%5] ^ rotl(C[(x+1)%5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x + 5*y] ^= D[x]

        # Rho + Pi
        new_state = [0]*25
        for x in range(5):
            for y in range(5):
                new_state[y + 5*((2*x+3*y)%5)] = rotl(
                    state[x + 5*y],
                    ROTATION_OFFSETS[x][y]
                )
        state = new_state

        # Chi
        for y in range(5):
            row = state[5*y:5*y+5]
            for x in range(5):
                state[5*y+x] ^= (~row[(x+1)%5]) & row[(x+2)%5]

        # Iota
        state[0] ^= rc

    return state

def keccak256_hash(message: str) -> str:
    """
    Calculate Keccak-256 hash of the given message.
    
    Args:
        message: Input message string
        
    Returns:
        Keccak-256 hash as hexadecimal string
    """
    if isinstance(message, str):
        message = message.encode('utf-8')
        
    rate = 1088 // 8  # 136 bytes
    state = [0] * 25

    # Padding (Keccak padding: 0x01 ... 0x80)
    padded = bytearray(message)
    padded.append(0x01)
    while len(padded) % rate != rate - 1:
        padded.append(0x00)
    padded.append(0x80)

    # Absorb phase
    for i in range(0, len(padded), rate):
        block = padded[i:i+rate]
        for j in range(len(block)):
            state[j//8] ^= block[j] << (8*(j%8))
        state = keccak_f(state)

    # Squeeze phase
    output = bytearray()
    while len(output) < 32:
        for i in range(rate):
            output.append((state[i//8] >> (8*(i%8))) & 0xFF)
        if len(output) >= 32:
            break
        state = keccak_f(state)

    return output[:32].hex()[:64]





# ==========================================
# Curve Parameters (secp256k1)
# ==========================================


# ==========================================
# Utility Functions
# ==========================================

def inverse_mod(k, mod):
    return pow(k % mod, -1, mod)

def is_on_curve(P):
    if P is None:
        return True
    x, y = P
    return (y * y - (x * x * x + a * x + b)) % p == 0

def point_add(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P

    x1, y1 = P
    x2, y2 = Q

    if x1 == x2 and (y1 + y2) % p == 0:
        return None

    if P == Q:
        if y1 == 0:
            return None
        m = (3 * x1 * x1 + a) * inverse_mod((2 * y1) % p, p)
    else:
        m = (y2 - y1) * inverse_mod((x2 - x1) % p, p)

    m %= p
    x3 = (m * m - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)

def scalar_mult(k, P):
    result = None
    addend = P

    while k > 0:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1

    assert is_on_curve(result)
    return result

# ==========================================
# Key Generation
# ==========================================

def generate_keys():
    private_key = random.randrange(1, n)
    public_key = scalar_mult(private_key, G)
    return private_key, public_key

# ==========================================
# Sign
# ==========================================

def sign(message, private_key):
    z = int(sha256_hash(message), 16) % n

    while True:
        k = random.randrange(1, n)
        point = scalar_mult(k, G)
        if point is None:
            continue

        r = point[0] % n
        if r == 0:
            continue

        k_inv = inverse_mod(k, n)
        s = (k_inv * (z + r * private_key)) % n
        if s != 0:
            break

    return (r, s)

# ==========================================
# Verify
# ==========================================

def verify(message, signature, public_key):
    r, s = signature
    if not (1 <= r < n and 1 <= s < n):
        return False

    z = int(sha256_hash(message), 16) % n
    s_inv = inverse_mod(s, n)

    u1 = (z * s_inv) % n
    u2 = (r * s_inv) % n

    P = point_add(
        scalar_mult(u1, G),
        scalar_mult(u2, public_key)
    )

    if P is None:
        return False

    return (P[0] % n) == r