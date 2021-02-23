function showImage(thumbnailImgElement) {
  const possibleImages = mainImageContainer.querySelectorAll('.col');
  const possibleImageArray = Array.from(possibleImages);
  const mainImage = possibleImageArray.find(function(imgElement) {
    return !imgElement.hidden;
  });
  mainImage.hidden = true;
  const imageId = thumbnailImgElement.dataset.imageId;
  const actualImageElement = document.getElementById(imageId);
  actualImageElement.hidden = false;
}

let invert = 0;
let contrast = 1;
let tempContrast = contrast;
let brightness = 1;
let tempBrightness = brightness;

const imageViewPort = document.getElementById('image_view_port_id');
function setFilterStyle() {
  imageViewPort.style.setProperty(
      'filter',
      'invert(' + invert + ') ' +
      'contrast(' + tempContrast + ') ' +
      'brightness(' + tempBrightness + ')',
  );
}

document.getElementById('invert_button_id').onclick = function() {
  invert = 1 ^ invert;
  setFilterStyle();
};

const brightnessSliderElement = document.getElementById('brightness_slider_id');
brightnessSliderElement.oninput = function() {
  tempBrightness = this.value;
  setFilterStyle();
};

const contrastSliderElement = document.getElementById('contrast_slider_id');
contrastSliderElement.oninput = function() {
  tempContrast = this.value;
  setFilterStyle();
};

const modalElement = document.getElementById('tone_modal_id');
modalElement.addEventListener('hide.bs.modal', function() {
  tempContrast = contrast;
  tempBrightness = brightness;
  contrastSliderElement.value = contrast;
  brightnessSliderElement.value = brightness;
  setFilterStyle();
});

const modal = new bootstrap.Modal(modalElement);
const applyButton = document.getElementById('apply_image_editor_button_id');
applyButton.onclick = function() {
  contrast = tempContrast;
  brightness = tempBrightness;
  modal.hide();
};


let scale = 1;
let rotation = 0;
let translateX = 0;
let translateY = 0;

const imageHolder = document.getElementById('image_holder_id');
function setTransformStyle() {
  imageHolder.style.setProperty(
      'transform',
      'scale(' + scale + ') ' +
      'rotate(' + rotation + 'deg) ' +
      'translate(' + translateX + 'px, ' + translateY + 'px)',
  );
}

document.getElementById('zoom_in_id').onclick = function() {
  if (scale >= 26) {
    return;
  }
  scale *= 1.5;
  setTransformStyle();
};

document.getElementById('zoom_out_id').onclick = function() {
  if (scale <= 0.1) {
    return;
  }
  scale /= 1.5;
  setTransformStyle();
};

function mod(n, m) {
  return ((n % m) + m) % m;
}

document.getElementById('rotate_left_id').onclick = function() {
  rotation -= 90;
  rotation = mod(rotation, 360);
  setTransformStyle();
};

document.getElementById('rotate_right_id').onclick = function() {
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

const mainImageContainer = document.getElementById('main_image_container_id');
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
