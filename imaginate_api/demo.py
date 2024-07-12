from ImageHandler import ImageHandler
from schemas.image_info import ImageInfo

image_handler = ImageHandler()


def example():
  # queue up an image to be generated
  text_prompt = (
    "Generate a high-resolution, ultra-realistic image of a fresh grilled cheese sandwich. "
    "The sandwich has golden-brown, crispy bread with melted cheese oozing out. "
    "It is cut diagonally and placed on a rustic wooden board. "
    "The background is a cozy kitchen setting with warm lighting."
  )
  info = ImageInfo(
    filename="grilled_cheese.jpg", date=0, theme="grilled cheese", real=False
  )
  image_handler.enqueue_prompt_to_image(
    prompt=text_prompt, info=info, num_inference_steps=100
  )

  # end image handler processing
  image_handler.stop_processing()


if __name__ == "__main__":
  CHOICE = str(input("Do you want to run 'example', 'live', or 'check db'? ")).lower()
  if CHOICE == "example":
    example()
  if CHOICE == "live":
    while True:
      PROMPT = str(input("Enter prompt (exit to quit): "))
      if PROMPT != "exit":
        image_handler.enqueue_prompt_to_image(
          prompt=PROMPT,
          info=ImageInfo(filename="live.jpg", date=0, theme="live", real=False),
        )
      else:
        break

    image_handler.stop_processing()
  if CHOICE == "check db":
    import requests

    response = requests.get("http://127.0.0.1:5000/image/read", timeout=10)
    print(response.text)
