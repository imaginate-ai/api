import threading
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import requests

from imaginate_api.image_handler import ImageHandler, DataType
from schemas.image_info import ImageInfo
import io


@pytest.fixture(scope="module")
def image_handler():
  handler = ImageHandler()
  yield handler
  handler.stop_processing()


@pytest.fixture()
def mock_image():
  return Image.new("RGB", (100, 100))


@pytest.fixture()
def mock_info():
  return ImageInfo(
    filename="test.jpeg", real=True, date="2023-04-01", theme="test", status="new"
  )


def run_process_queue(handler):
  thread = threading.Thread(target=handler._process_queue)
  thread.start()
  thread.join()


@pytest.fixture
def mock_task_image():
  return {"type": DataType.IMAGE, "kwargs": {"image": mock_image}, "info": MagicMock()}


@pytest.fixture
def mock_task_prompt():
  return {
    "type": DataType.PROMPT,
    "kwargs": {"prompt": "test prompt"},
    "info": MagicMock(),
  }


# init
@pytest.fixture
def mock_device(mocker):
  return mocker.patch("torch.device", return_value="cpu")


@pytest.fixture
def mock_thread(mocker):
  return mocker.patch("threading.Thread", return_value=MagicMock())


@pytest.fixture
def mock_queue(mocker):
  return mocker.patch("queue.Queue", return_value=MagicMock())


@pytest.fixture
def mock_scheduler(mocker):
  return mocker.patch(
    "diffusers.EulerAncestralDiscreteScheduler.from_config", return_value=MagicMock()
  )


@pytest.fixture
def mock_stable_diffusion(mocker):
  return mocker.patch(
    "diffusers.StableDiffusionInstructPix2PixPipeline.from_pretrained",
    return_value=MagicMock().to.return_value,
  )


@pytest.fixture
def mock_diffusion_pipeline(mocker):
  return mocker.patch(
    "diffusers.DiffusionPipeline.from_pretrained",
    return_value=MagicMock().to.return_value,
  )


# get_image_from_url
def test_get_image_from_url_success(image_handler, mock_image):
  with (
    patch("requests.get") as mock_get,
    patch("PIL.Image.open") as mock_open,
    patch("PIL.ImageOps.exif_transpose") as mock_exif_transpose,
  ):
    mock_response = MagicMock()
    mock_response.raw = io.BytesIO(b"fake image data")
    mock_get.return_value = mock_response
    mock_open.return_value = mock_image
    mock_exif_transpose.return_value = mock_image

    url = "http://fakeurl.com/image.jpg"
    result_image = image_handler.get_image_from_url(url)

    assert isinstance(result_image, Image.Image)
    mock_get.assert_called_once_with(url, stream=True, timeout=10)
    mock_open.assert_called_once()
    mock_exif_transpose.assert_called_once_with(mock_image)


def test_get_image_from_url_timeout_exception(image_handler):
  with patch("requests.get", side_effect=requests.exceptions.Timeout) as mock_get:
    url = "http://fakeurl.com/image.jpg"
    with pytest.raises(requests.exceptions.Timeout):
      image_handler.get_image_from_url(url)
    mock_get.assert_called_once()


def test_get_image_from_url_invalid_url(image_handler):
  with patch("requests.get", side_effect=requests.exceptions.InvalidURL) as mock_get:
    url = "http://invalidurl"
    with pytest.raises(requests.exceptions.InvalidURL):
      image_handler.get_image_from_url(url)
    mock_get.assert_called_once()


# enqueue_image_to_image
def test_enqueue_image_to_image_with_image_object(image_handler, mock_image, mock_info):
  with patch.object(image_handler.queue, "put") as mock_put:
    image_handler.enqueue_image_to_image(info=mock_info, image=mock_image)
    task = mock_put.call_args[0][0]
    assert task["type"] == DataType.IMAGE
    assert task["kwargs"]["image"] == mock_image
    assert task["info"] == mock_info


def test_enqueue_image_to_image_with_image_url(image_handler, mock_image, mock_info):
  with (
    patch.object(
      image_handler, "get_image_from_url", return_value=mock_image
    ) as mock_get_image,
    patch.object(image_handler.queue, "put") as mock_put,
  ):
    url = "http://fakeurl.com/image.jpg"
    image_handler.enqueue_image_to_image(info=mock_info, image=url)
    mock_get_image.assert_called_once_with(url)
    task = mock_put.call_args[0][0]
    assert task["type"] == DataType.IMAGE
    assert task["kwargs"]["image"] == mock_image
    assert task["info"] == mock_info


def test_enqueue_image_to_image_missing_optional_params(
  image_handler, mock_image, mock_info
):
  with patch.object(image_handler.queue, "put") as mock_put:
    image_handler.enqueue_image_to_image(info=mock_info, image=mock_image)
    task = mock_put.call_args[0][0]
    assert "prompt" in task["kwargs"]
    assert "num_inference_steps" not in task["kwargs"]
    assert "image_guidance_scale" not in task["kwargs"]


def test_enqueue_image_to_image_queue_enqueue(image_handler, mock_image, mock_info):
  with patch.object(image_handler.queue, "put") as mock_put:
    image_handler.enqueue_image_to_image(info=mock_info, image=mock_image)
    mock_put.assert_called_once()
    task = mock_put.call_args[0][0]
    assert task["type"] == DataType.IMAGE
    assert task["info"] == mock_info
    assert task["kwargs"]["image"] == mock_image


# enqueue_prompt_to_image
def test_enqueue_prompt_to_image_with_required_params(image_handler, mock_info):
  with patch.object(image_handler.queue, "put") as mock_put:
    prompt = "test prompt"
    image_handler.enqueue_prompt_to_image(info=mock_info, prompt=prompt)
    mock_put.assert_called_once()
    task = mock_put.call_args[0][0]
    assert task["type"] == DataType.PROMPT
    assert task["kwargs"]["prompt"] == prompt
    assert task["info"] == mock_info


def test_enqueue_prompt_to_image_with_all_params(image_handler, mock_info):
  with patch.object(image_handler.queue, "put") as mock_put:
    prompt = "test prompt"
    negative_prompt = "not this"
    num_inference_steps = 50
    guidance_scale = 7.5
    image_handler.enqueue_prompt_to_image(
      info=mock_info,
      prompt=prompt,
      negative_prompt=negative_prompt,
      num_inference_steps=num_inference_steps,
      guidance_scale=guidance_scale,
    )
    mock_put.assert_called_once()
    task = mock_put.call_args[0][0]
    assert task["kwargs"]["prompt"] == prompt
    assert task["kwargs"]["negative_prompt"] == negative_prompt
    assert task["kwargs"]["num_inference_steps"] == num_inference_steps
    assert task["kwargs"]["guidance_scale"] == guidance_scale


def test_enqueue_prompt_to_image_queue_enqueue(image_handler, mock_info):
  with patch.object(image_handler.queue, "put") as mock_put:
    image_handler.enqueue_prompt_to_image(info=mock_info, prompt="test prompt")
    mock_put.assert_called_once()


def test_enqueue_prompt_to_image_task_structure(image_handler, mock_info):
  with patch.object(image_handler.queue, "put") as mock_put:
    prompt = "test prompt"
    image_handler.enqueue_prompt_to_image(info=mock_info, prompt=prompt)
    task = mock_put.call_args[0][0]
    assert task["type"] == DataType.PROMPT
    assert "prompt" in task["kwargs"]
    assert task["info"] == mock_info


def test_enqueue_prompt_to_image_missing_prompt(image_handler, mock_info):
  with patch.object(image_handler.queue, "put") as mock_put:
    with pytest.raises(ValueError):
      image_handler.enqueue_prompt_to_image(info=mock_info, prompt=None)
    mock_put.assert_not_called()


# process_queue
def test_process_queue_with_image_task(image_handler, mock_task_image):
  with (
    patch.object(image_handler.queue, "get", side_effect=[mock_task_image, None]),
    patch.object(image_handler, "process") as mock_process,
    patch.object(image_handler.queue, "task_done") as mock_task_done,
  ):
    run_process_queue(image_handler)
    mock_process.assert_called_once_with(mock_task_image)
    mock_task_done.assert_called_once()


def test_process_queue_with_prompt_task(image_handler, mock_task_prompt):
  with (
    patch.object(image_handler.queue, "get", side_effect=[mock_task_prompt, None]),
    patch.object(image_handler, "process") as mock_process,
    patch.object(image_handler.queue, "task_done") as mock_task_done,
  ):
    run_process_queue(image_handler)
    mock_process.assert_called_once_with(mock_task_prompt)
    mock_task_done.assert_called_once()


def test_process_queue_stops_after_none(image_handler):
  with (
    patch.object(image_handler.queue, "get", return_value=None),
    patch.object(image_handler, "process") as mock_process,
    patch.object(image_handler.queue, "task_done") as mock_task_done,
  ):
    run_process_queue(image_handler)
    mock_process.assert_not_called()
    mock_task_done.assert_not_called()


def test_enqueue_image_to_image_with_optional_params(
  image_handler, mock_info, mock_image
):
  with patch.object(image_handler.queue, "put") as mock_put:
    valid_image = mock_image
    image_handler.enqueue_image_to_image(
      info=mock_info,
      image=valid_image,
      prompt="test prompt",
      num_inference_steps=50,
      image_guidance_scale=7.5,
    )
    assert mock_put.called
    task = mock_put.call_args[0][0]
    assert task["kwargs"]["prompt"] == "test prompt"
    assert task["kwargs"]["num_inference_steps"] == 50
    assert task["kwargs"]["image_guidance_scale"] == 7.5


def test_enqueue_prompt_to_image_with_optional_params(image_handler, mock_info):
  with patch.object(image_handler.queue, "put") as mock_put:
    image_handler.enqueue_prompt_to_image(
      info=mock_info,
      prompt="test prompt",
      negative_prompt="negative test prompt",
      num_inference_steps=50,
      guidance_scale=7.5,
    )
    assert mock_put.called
    task = mock_put.call_args[0][0]
    assert task["kwargs"]["negative_prompt"] == "negative test prompt"
    assert task["kwargs"]["num_inference_steps"] == 50
    assert task["kwargs"]["guidance_scale"] == 7.5


def test_process_queue_with_empty_queue(image_handler):
  with (
    patch.object(image_handler.queue, "get", side_effect=[None]),
    patch.object(image_handler, "process") as mock_process,
  ):
    run_process_queue(image_handler)
    mock_process.assert_not_called()


def test_process_queue_with_invalid_task(image_handler):
  with patch.object(image_handler.queue, "put") as mock_put:
    with pytest.raises(ValueError):
      image_handler.enqueue_prompt_to_image(info=mock_info, prompt=None)
    mock_put.assert_not_called()


def test_enqueue_image_to_image_task_structure(image_handler, mock_info, mock_image):
  with patch.object(image_handler.queue, "put") as mock_put:
    valid_image = mock_image
    image_handler.enqueue_image_to_image(info=mock_info, image=valid_image)
    assert mock_put.called
    task = mock_put.call_args[0][0]
    assert "type" in task
    assert "kwargs" in task
    assert "info" in task
    assert task["type"] == DataType.IMAGE
