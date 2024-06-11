from ImageHandler import ImageHandler

image_handler = ImageHandler()

def example():
    # image 1
    url = ('https://raw.githubusercontent.com/timothybrooks/instruct-pix2pix/main/imgs/example.jpg')
    image_handler.enqueue_image_to_image(init_image=url, prompt='turn him into a cyborg', num_inference_steps=10, guidance_scale=1)

    # image 2
    prompt = (
        "Generate a high-resolution, ultra-realistic image of a freshly made grilled cheese sandwich. "
        "The sandwich has golden-brown, crispy bread with melted cheese oozing out. "
        "It is cut diagonally and placed on a rustic wooden board. "
        "The background is a cozy kitchen setting with warm lighting."
    )
    image_handler.enqueue_prompt_to_image(prompt=prompt)

    # image 3
    prompt = (
        """
        Generate an image of a bowl of fancy soup. The soup should be presented elegantly in a clean and minimalist style. The bowl should be made of white porcelain and placed on a wooden table. The soup should be a creamy texture, with a vibrant orange color. Garnish the soup with a sprinkle of fresh chives and a swirl of high-quality olive oil on the surface.
        """
    )
    image_handler.enqueue_prompt_to_image(prompt=prompt, guidance_scale=10)

    # end image handler processing
    image_handler.stop_processing()

if __name__ == '__main__':
    choice = str(input("Do you want to run 'example' or 'live'? ")).lower()
    if choice == 'example':
        example()
    else:
        while True:
            prompt = str(input("Enter prompt (exit to quit): "))
            if not prompt == 'exit':
                image_handler.enqueue_prompt_to_image(prompt=prompt)
            else:
                break
        
        image_handler.stop_processing()