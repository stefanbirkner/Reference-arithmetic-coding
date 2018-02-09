import arithmeticcoding
import os
import sys
python3 = sys.version_info.major >= 3


def main(args):
    # Handle command line arguments
    if len(args) != 1:
        sys.exit("Usage: python bit-rate.py Folder")
    root_dir = args[0]
    stats = []
    num_pixels = 1  # change to image size here
    for dirName, _, fileList in os.walk(root_dir):
        for name in fileList:
            if name.endswith('.txt'):
                filename = dirName + "/" + name
                bit_rate_adaptive = (calculate_num_bits_adaptive(filename) * 8) / num_pixels
                bit_rate_simple = (calculate_num_bits_simple(filename) * 8) / num_pixels
                stats.append((filename, bit_rate_adaptive, bit_rate_simple))
                print('\t%s - %d, %d' % (filename, bit_rate_adaptive, bit_rate_simple))
    write_stats(root_dir, stats)

def calculate_num_bits_adaptive(inputfile):
    outputfile = "/tmp/bitrate"
    with open(inputfile, "rb") as inp:
        bitout = arithmeticcoding.BitOutputStream(open(outputfile, "wb"))
        try:
            compress_adaptive(inp, bitout)
        finally:
            bitout.close()
    return os.path.getsize(outputfile)


def compress_adaptive(inp, bitout):
    initfreqs = arithmeticcoding.FlatFrequencyTable(257)
    freqs = arithmeticcoding.SimpleFrequencyTable(initfreqs)
    enc = arithmeticcoding.ArithmeticEncoder(bitout)
    while True:
        # Read and encode one byte
        symbol = inp.read(1)
        if len(symbol) == 0:
            break
        symbol = symbol[0] if python3 else ord(symbol)
        enc.write(freqs, symbol)
        freqs.increment(symbol)
    enc.write(freqs, 256)  # EOF
    enc.finish()  # Flush remaining code bits


def calculate_num_bits_simple(inputfile):
    freqs = get_frequencies(inputfile)
    freqs.increment(256)  # EOF symbol gets a frequency of 1

    outputfile = "/tmp/bitrate"
    with open(inputfile, "rb") as inp:
        bitout = arithmeticcoding.BitOutputStream(open(outputfile, "wb"))
        try:
            compress_simple(freqs, inp, bitout)
        finally:
            bitout.close()
    return os.path.getsize(outputfile)


# Returns a frequency table based on the bytes in the given file.
# Also contains an extra entry for symbol 256, whose frequency is set to 0.
def get_frequencies(filepath):
    freqs = arithmeticcoding.SimpleFrequencyTable([0] * 257)
    with open(filepath, "rb") as input:
        while True:
            b = input.read(1)
            if len(b) == 0:
                break
            b = b[0] if python3 else ord(b)
            freqs.increment(b)
    return freqs


def write_frequencies(bitout, freqs):
    for i in range(256):
        write_int(bitout, 32, freqs.get(i))


def compress_simple(freqs, inp, bitout):
    enc = arithmeticcoding.ArithmeticEncoder(bitout)
    while True:
        symbol = inp.read(1)
        if len(symbol) == 0:
            break
        symbol = symbol[0] if python3 else ord(symbol)
        enc.write(freqs, symbol)
    enc.write(freqs, 256)  # EOF
    enc.finish()  # Flush remaining code bits


# Writes an unsigned integer of the given bit width to the given stream.
def write_int(bitout, numbits, value):
    for i in reversed(range(numbits)):
        bitout.write((value >> i) & 1)  # Big endian


def write_stats(dirname, stats):
    with open(dirname + "/stats.csv", "w") as text_file:
        for single_stats in stats:
            text_file.write("%s,%f,%f" % single_stats)

# Main launcher
if __name__ == "__main__":
    main(sys.argv[1:])
