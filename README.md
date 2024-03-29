# Tokenizer

Finetune here to talk a bit about our new tokenizer that I worked on. First a quick reminder. In most cases, our models don't see words as individual letters. Instead, text is broken down into tokens, which are words or word fragments. For example, the sentence “`The quick brown fox jumps over the goblin.`” would tokenize as “`The| quick| brown| fox| jumps| over| the| go|bl|in.`” in the Pile tokenizer used by GPT-NeoX 20B and Krake, with each | signifying a boundary between tokens.

When deciding on a tokenizer for a model, there are various criteria to consider. The first and most obvious is the vocabulary size. It may be tempting to just set it very high to ensure that every word or even multiple words, as in the case of the tokenizer used by AI21's Jurassic models, gets its own distinct token. However, this has the drawback that the model will be less able to generalize. That means it will not be able to make use of meaningful patterns in how words are spelt, such as similarities between words ending in “-ize”. It will also be less robust against misspellings. At the same time, the vocabulary of the tokenizer should not be too small. Common words should have their own token. The same goes for Unicode characters that are likely to show up in tokenized texts, because otherwise they will have to be constructed by the model byte-by-byte, which is much harder for the model. A good trade-off with regards to vocabulary size is around 32000 tokens for a single language vocabulary. This also has the benefit of fitting easily within 16 bits, which makes handling tokenized data easier in many cases.

The type of tokenizer is another important decision to make. Unigram tokenizers have been shown to produce much more meaningful tokenizations of words, while so far the predominantly used tokenizer type for large language models (LLM) is BPE (byte pair encoding). The most common implementation of BPE is probably the GPT2 one, but Google's sentencepiece implementation of BPE offers the not so slight advantage of natively being able to tokenize Unicode characters directly, without having to assemble them from bytes, which requires additional tokens representing partial Unicode code points to be added to the vocabulary, wasting some additional space. For example, “🙂” consists of four bytes “`F0 9F 99 82`”, so in traditional BPE, `F0` would first get merged with `9F` to make up `F09F`, which is then merged with `99` to make up `F09F99`, which is then merged with `82`, so two additional intermediate tokens would have to be added to the vocabulary. At the same time, sentencepiece also supports tokenizing arbitrary binary data using byte tokens.

Finally, the compression ratio achieved by the tokenizer is important to consider. If a given text tokenizes into less tokens, this will allow the LLM to see more text at once, given the fixed size of context it can see at a maximum, which is important for users of the LLm. It will also influence how much text you need to achieve a certain amount of tokens if, say, you are trying to meet a certain amount of training data. If your tokenizer compresses text less efficiently, you may more easily achieve a dataset of a given size, but it stands to reason that a model trained on such a less efficiently tokenized dataset of a given size will learn less than one trained of on a same sized dataset that was tokenized with a tokenizer that achieves a higher compression ratio, because in effect, it will see less bits of actually information during training.

With all these things in mind, we decided that we want our own tokenizer for the models we will train, that is better optimized for our use cases, such as storytelling.

Tokenizers are trained on data, so we started by extracting small randomized subsets from the various distinct subsets of our model training dataset and used these to evaluate the available tokenizer training approaches. Both Huggingface's tokenizers library and Google's sentencepiece support training tokenizers of different types. A preliminary investigation showed that sentencepiece's trainer is more memory efficient, although a training dataset in the low double digit gibibytes still required a compute node with 1TB of RAM to run successfully. Due to this, we decided to use sentencepiece.

We originally decided on a vocabulary size of 32000, but when training Genji V2, we found that modifying an existing tokenizer to support an additional language was not a pleasant experience. As it seems likely that we will want to do similar [language transfer learning](https://blog.novelai.net/data-efficient-language-transfer-with-gpt-j-45daedaaf35a) in the future, we have decided to have our tokenizer accommodate both English and Japanese from the start. For this reason, we decided to double the vocabulary size to 64000, which then was close to filling up the available token ID space of 16 bits, so we went all the way to a vocabulary size of 65535 tokens. During tokenizer training, I carefully balanced the training data in such a way that latin alphabet tokens of a length of at least 2 characters and Japanese language tokens take up approximately the same amount of token space. Bumping the vocabulary size up to 65535 also allows more Unicode character tokens such as emoji. For the Japanese part of tokenizer training data, we used our existing Genji training data and a comparatively smaller amount of Japanese Wikipedia.

We have manually added tokens for certain multi-whitespace strings and have set up the tokenizer in such a way that numbers are tokenized digit by digit. Tokenizing numbers digit by digit may slightly reduce compression ratio in number heavy texts, but it will also allow the LLM to more effectively learn how to handle numeric values.

Considering the possible benefits of Unigram tokenizers, we started out by training a Unigram tokenizer. This took multiple runs of rebalancing the dataset between languages and also between the different subsets of our main datasets to get the token distribution to look the way we want. Each Unigram training run took a few hours. For the sake of comparison, we also trained a BPE model, which again required multiple runs to rebalance the dataset. BPE runs ended up much slower, taking nearly a whole day.

Both tokenizers were then evaluated on a held-out part of the dataset. The idea was that, if the compression ratios are similar or Unigram is only slightly worse, we would use the Unigram tokenizer to benefit from the more natural word segmentation. We found that the BPE tokenizer has a 25-29% higher compression ratio on the largest parts of our English language dataset. This unexpectedly large gap in performance led us to choose the BPE tokenizer over the Unigram one and also explains the continuing prevalence of BPE tokenizers for LLMs. We also compared the compression ratio of our tokenizer to the LLaMa tokenizer, which is a sentencepiece based BPE tokenizer with a 32000 token vocabulary. In comparison to the LLaMa tokenizer, we find our tokenizer to achieve a 7-19% higher compression ratio on the largest parts of our English language dataset.

Finally, I would like to give some stats about token distribution. Our tokenizer contains 28586 tokens made up of latin alphabet characters with a minimum length of two. Tokens with a leading space are included in this. It contains 18123 Japanese tokens longer than a single character and 9626 tokens for Japanese and Chinese characters, which cannot be easily told apart for the sake of these stats due to the Unicode han unification. 9200 other tokens are included. This space is taken up mostly by Unicode characters such as emoji.

For comparison, the LLaMa tokenizer contains 23964 tokens made up only of latin alphabet characters, no Japanese token longer than a single character, 836 Japanese characters and 7224 other tokens.

## JavaScript implementation

The JavaScript implementation used by the NovelAI frontend can be found [here](https://github.com/NovelAI/nai-js-tokenizer).

## V2

For V2, the original digit special tokens were replaced with english contractions. Digits will therefore be encoded using corresponding the byte tokens instead.

## Huggingface

Our tokenizer is also available on Huggingface Hub:

* https://huggingface.co/NovelAI/nerdstash-tokenizer-v1
* https://huggingface.co/NovelAI/nerdstash-tokenizer-v2

## License

The tokenizer is licensed under the GNU General Public License, version 2.
