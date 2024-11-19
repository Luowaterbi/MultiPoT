python compare.py \
    --datasets gsm,math \
    --langs python,r,java,cpp,js \
    --examples fewshot \
    --output_suffix _ans \
    --middle_dir outputs_llama3_1_8b \
    --multi \
    --opt vote

python compare.py \
    --datasets gsm,math \
    --langs python \
    --examples fewshot \
    --output_suffix _ans \
    --middle_dir outputs_llama3_1_8b \
    --opt best