let invert = 0;
let contrast = 1;
let tempContrast = contrast;
let brightness = 1;
let tempBrightness = brightness;

const imageViewPort = document.getElementById('id_image_view_port');
function setFilterStyle() {
  imageViewPort.style.setProperty(
      'filter',
      'invert(' + invert + ') ' +
      'contrast(' + tempContrast + ') ' +
      'brightness(' + tempBrightness + ')',
  );
}

document.getElementById('id_invert_button').onclick = function() {
  invert = 1 ^ invert;
  setFilterStyle();
};

const brightnessSliderElement = document.getElementById('id_brightness_slider');
brightnessSliderElement.oninput = function() {
  tempBrightness = this.value;
  setFilterStyle();
};

const contrastSliderElement = document.getElementById('id_contrast_slider');
contrastSliderElement.oninput = function() {
  tempContrast = this.value;
  setFilterStyle();
};

const modalElement = document.getElementById('id_tone_modal');
modalElement.addEventListener('hide.bs.modal', function() {
  tempContrast = contrast;
  tempBrightness = brightness;
  contrastSliderElement.value = contrast;
  brightnessSliderElement.value = brightness;
  setFilterStyle();
});

const modal = new bootstrap.Modal(modalElement);
const applyButton = document.getElementById('id_apply_image_editor_button');
applyButton.onclick = function() {
  contrast = tempContrast;
  brightness = tempBrightness;
  modal.hide();
};


let scale = 1;
let rotation = 0;
let translateX = 0;
let translateY = 0;

const imageHolder = document.getElementById('id_image_holder');
function setTransformStyle() {
  imageHolder.style.setProperty(
      'transform',
      'scale(' + scale + ') ' +
      'rotate(' + rotation + 'deg) ' +
      'translate(' + translateX + 'px, ' + translateY + 'px)',
  );
}

document.getElementById('id_zoom_in').onclick = function() {
  if (scale >= 26) {
    return;
  }
  scale *= 1.5;
  setTransformStyle();
};

document.getElementById('id_zoom_out').onclick = function() {
  if (scale <= 0.1) {
    return;
  }
  scale /= 1.5;
  setTransformStyle();
};

function mod(n, m) {
  return ((n % m) + m) % m;
}

document.getElementById('id_rotate_left').onclick = function() {
  rotation -= 90;
  rotation = mod(rotation, 360);
  setTransformStyle();
};

document.getElementById('id_rotate_right').onclick = function() {
  rotation += 90;
  rotation = mod(rotation, 360);
  setTransformStyle();
};


let originalMouseX = 0;
let originalMouseY = 0;

const rotationFuncMap = {
  0: function(x, y) {
    translateX -= (originalMouseX - x) / scale;
    translateY -= (originalMouseY - y) / scale;
  },
  90: function(x, y) {
    translateY += (originalMouseX - x) / scale;
    translateX -= (originalMouseY - y) / scale;
  },
  180: function(x, y) {
    translateX += (originalMouseX - x) / scale;
    translateY += (originalMouseY - y) / scale;
  },
  270: function(x, y) {
    translateY -= (originalMouseX - x) / scale;
    translateX += (originalMouseY - y) / scale;
  },
};

const mainImageContainer = document.getElementById('id_main_image_container');
mainImageContainer.onpointerdown = function(event) {
  event = event || window.event;
  event.preventDefault();
  originalMouseX = event.clientX;
  originalMouseY = event.clientY;
  document.onpointerup = function() {
    document.onpointerup = null;
    document.onpointermove = null;
  };
  document.onpointermove = function(event) {
    event = event || window.event;
    event.preventDefault();
    rotationFuncMap[rotation](event.clientX, event.clientY);
    originalMouseX = event.clientX;
    originalMouseY = event.clientY;
    setTransformStyle();
  };
};
mainImageContainer.ontouchstart = function(event) {
  if (mainImageContainer == event.target || event.target.hidden) {
    event.preventDefault();
  }
};

const toastContainer = document.getElementById('id_toast_container');
function createToast(message, backgroundColor, options) {
  const toastDiv = document.createElement('div');
  toastDiv.classList.add('toast', 'align-items-center', 'text-white', backgroundColor, 'border-0');
  toastDiv.setAttribute('role', 'alert');

  const formatDiv = document.createElement('div');
  formatDiv.classList.add('d-flex');

  const toastBody = document.createElement('div');
  toastBody.classList.add('toast-body');
  toastBody.innerText = message;

  const closeButton = document.createElement('button');
  closeButton.type = 'button';
  closeButton.classList.add('btn-close', 'btn-close-white', 'me-2', 'm-auto');
  closeButton.setAttribute('data-bs-dismiss', 'toast');

  toastDiv.appendChild(formatDiv);
  formatDiv.appendChild(toastBody);
  formatDiv.appendChild(closeButton);

  const bootstrapToast = new bootstrap.Toast(toastDiv, options);
  toastDiv.addEventListener('hidden.bs.toast', function () {
    toastDiv.remove();
  });
  bootstrapToast.show();

  toastContainer.prepend(toastDiv);
}

let imageShowing = null;
const images = [];
const thumbnailsDiv = document.getElementById('id_thumbnails');
const imageHolderDiv = document.getElementById('id_image_holder');
function addImage(thumbnailUrl, imageUrl) {
  const idNum = imageHolderDiv.childElementCount;
  const imageDivId = 'id_image_' + idNum;

  const mainImageDiv = document.createElement('div');
  mainImageDiv.classList.add('col')
  mainImageDiv.id = imageDivId;
  if (idNum !== 0) {
    mainImageDiv.hidden = true;
    imageShowing = mainImageDiv;
  } else {
    mainImageContainer.hidden = false;
  }

  const mainImageElement = document.createElement('img');
  mainImageElement.src = imageUrl;
  mainImageElement.classList.add('img-fluid');

  const thumbnailImgElement = document.createElement('img');
  thumbnailImgElement.id = 'id_thumbnail_' + idNum;
  thumbnailImgElement.src = thumbnailUrl;
  thumbnailImgElement.classList.add('img-thumbnail', 'w-24', 'w-md-100');
  thumbnailImgElement.onclick = function() {
    imageShowing.hidden = true;
    imageShowing = mainImageDiv;
    imageShowing.hidden = false;
  }

  mainImageDiv.appendChild(mainImageElement);
  imageHolderDiv.appendChild(mainImageDiv);
  thumbnailsDiv.appendChild(thumbnailImgElement);
}


const heightProperties = [
  'margin-top',
  'margin-bottom',
  'border-top',
  'border-bottom',
  'padding-top',
  'padding-bottom',
  'height'
]
function getElementHeight(element) {
  const style = window.getComputedStyle(element)
  return heightProperties
      .map(propertyName => parseInt(style.getPropertyValue(propertyName), 10))
      .reduce((prev, cur) => prev + cur)
}


const headerDiv = document.getElementById('id_header');
const inputRowDiv = document.getElementById('id_input_row');
const mainImageDiv = document.getElementById('id_main_image_container');
function setImageViewerHeight() {
  mainImageDiv.style.height = (
    window.innerHeight
    - getElementHeight(inputRowDiv)
    - getElementHeight(headerDiv)
    + getElementHeight(toastContainer)
  ) + "px";
}

setImageViewerHeight();

window.onresize = function() {
  setImageViewerHeight()
}
