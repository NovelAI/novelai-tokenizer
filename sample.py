import sentencepiece as spm

s = spm.SentencePieceProcessor(model_file='novelai_v2.model')

text = "The quick brown fox jumps over the goblin."

print("Text:", text)

print("Token IDs:", s.encode(text))
# Token IDs: [541, 1939, 6573, 22820, 22734, 712, 336, 34477, 49230]

print("Readable tokens:", s.encode(text, out_type=str))
# Readable tokens: ['The', '▁quick', '▁brown', '▁fox', '▁jumps', '▁over', '▁the', '▁goblin', '.']
