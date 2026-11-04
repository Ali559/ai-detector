# Bundled weights

`univfd_fc.pth`: the 768→1 linear probe from UnivFD ("Towards Universal Fake Image Detectors that Generalize Across Generative Models", Ojha, Li & Lee, CVPR 2023), copied from https://github.com/WisconsinAIVision/UniversalFakeDetect (`pretrained_weights/fc_weights.pth`). MIT License; see `app/vendor/univfd/LICENSE`.

Everything else in this directory is downloaded from Hugging Face at startup and is not committed:

| Head | Model | License |
| --- | --- | --- |
| face | `opencv/face_detection_yunet` (YuNet) | MIT |
| face | `yermandy/GenD_PE_L` (+ `timm/vit_pe_core_large_patch14_336.fb` backbone) | MIT (GenD); Apache 2.0 (Perception Encoder) |
| scene | `openai/clip-vit-large-patch14` | MIT |
| temporal | `microsoft/xclip-base-patch16` | MIT |
