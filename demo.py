import torch
from diffusers import AutoPipelineForImage2Image
from diffusers.utils import load_image, make_image_grid

# The model will be running locally!
# Code is following documentation provided here: https://huggingface.co/docs/diffusers/main/en/using-diffusers/img2img

# Set up pipeline
pipeline = AutoPipelineForImage2Image.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
pipeline.to("cuda")

# Pass prompt and image to pipeline
init_image = load_image("https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/cat.png")
images = pipeline("Recreate this image", image=init_image)
image = images[0]
make_image_grid([init_image, image], rows=1, cols=2)