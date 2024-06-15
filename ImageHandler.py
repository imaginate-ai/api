import contextlib
import requests
import queue
import io
import threading
from typing import Union
import PIL 
import torch
from enum import Enum

# Suppress saftey warnings and pipeline downloads
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from diffusers import AutoPipelineForText2Image, StableDiffusionInstructPix2PixPipeline, EulerAncestralDiscreteScheduler


class DataType(Enum):
    IMAGE = "image"
    PROMPT = "prompt"

class ImageHandler:
    

    def __init__(self):
        # provide support for both cuda and cpu
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Initialized for {self.device}")

        # Suppress warnings and model outputs
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):

            # Image to Image model
            # https://huggingface.co/timbrooks/instruct-pix2pix
            # https://github.com/timothybrooks/instruct-pix2pix/tree/main
            image_model_id = "timbrooks/instruct-pix2pix"
            self.image_pipe = StableDiffusionInstructPix2PixPipeline.from_pretrained(
                image_model_id, torch_dtype=torch.float16, safety_checker=None
            ).to(self.device)
            self.image_pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(self.image_pipe.scheduler.config)

            # Text to Image model
            # https://huggingface.co/runwayml/stable-diffusion-v1-5
            # https://github.com/runwayml/stable-diffusion
            text_model_id = "runwayml/stable-diffusion-v1-5"
            self.text_pipe = AutoPipelineForText2Image.from_pretrained(
                text_model_id, torch_dtype=torch.float16, safety_checker=None
            ).to(self.device)
            self.text_pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(self.image_pipe.scheduler.config)
            
            # Initialize the asynchronous queue and thread
            self.queue = queue.Queue()
            self.thread = threading.Thread(target=self._process_queue)
            self.thread.daemon = True
            self.thread.start()


    # Function to get image from url
    def get_image_from_url(self, url: str) -> PIL.Image.Image:
        image = PIL.Image.open(requests.get(url, stream=True).raw)
        image = PIL.ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        return image
    

    # Function to add image to image task to queue
    def enqueue_image_to_image(
        self, 
        image: Union[PIL.Image.Image, str], 
        prompt = 'make photograph', 
        num_inference_steps=None, 
        image_guidance_scale=None
    ):
        
        if isinstance(image, str):
            image = self.get_image_from_url(image)
        kwargs = {k: v for k, v in locals().items() if v and v is not self}

        task = {'type': DataType.IMAGE, 'kwargs': kwargs}
        self.queue.put(task)
        print(f"\nEnqueued: {prompt}")


    # Function to add text to image task to queue
    def enqueue_prompt_to_image(
        self, 
        prompt: str, 
        negative_prompt = None, 
        num_inference_steps=None, 
        guidance_scale=None
    ):
        
        kwargs = {k: v for k, v in locals().items() if v and v is not self}

        task = {'type': DataType.PROMPT, 'kwargs': kwargs}
        self.queue.put(task)
        print(f"\nEnqueued: {prompt}")
    

    # Continuously process the queue
    def _process_queue(self):
        while True:
            task = self.queue.get()
            if task:
                print(f"\nDequeued: {task['kwargs']['prompt']}")
                self.process(task)
                self.queue.task_done()
            else:
                break


    # Process the task
    def process(self, item):
        if item['type'] == DataType.IMAGE:
            image = self.image_pipe(**item['kwargs']).images[0]
        elif item['type'] == DataType.PROMPT:
            image = self.text_pipe(**item['kwargs']).images[0]

        image.show()


    # Stop processing the queue, wait for all tasks to finish
    def stop_processing(self):
        size = self.queue.qsize() + 1 if self.queue.qsize() > 0 else 0
        print(f"\nWaiting for {size} tasks to finish...")
        self.queue.put(None)
        self.thread.join()


