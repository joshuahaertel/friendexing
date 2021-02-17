function showImage(thumbnailImgElement) {
  const mainImageContainer = document.querySelector("#image-holder")
  const possibleImages = mainImageContainer.querySelectorAll(".col")
  const possibleImageArray = Array.from(possibleImages)
  const mainImage = possibleImageArray.find((imgElement) => !imgElement.hidden)
  mainImage.hidden = true
  const imageId = thumbnailImgElement.dataset.imageId
  const actualImageElement = document.querySelector(imageId)
  actualImageElement.hidden = false
}
