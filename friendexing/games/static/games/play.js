const thumbnails = document.querySelectorAll('.img-thumbnail');
thumbnails.forEach(function(thumbnail) {
  thumbnail.onclick = function() {
    const possibleImages = mainImageContainer.querySelectorAll('.col');
    const possibleImageArray = Array.from(possibleImages);
    const mainImage = possibleImageArray.find(function(imgElement) {
      return !imgElement.hidden;
    });
    mainImage.hidden = true;
    const imageId = this.dataset.imageId;
    const actualImageElement = document.getElementById(imageId);
    actualImageElement.hidden = false;
  };
});

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

const gameId = window.location.pathname.split("/")[2]

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}

const playerId = getCookie(gameId);

function getSocket() {
  const playerSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/play/'
    + gameId
    + '/'
    + playerId
    + '/'
  );

  const scores = document.getElementById('id_scores');
  playerSocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    scores.innerHTML = "";
    data.scores.forEach(function(score) {
      scores.innerHTML += '<p>' + score.score + ' - ' + score.name + '</p>';
    })
  }

  playerSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly, refresh browser');
  };
  return playerSocket
};

const playerSocket = getSocket();

const submitButton = document.getElementById('id_submit');
const guessTextBox = document.getElementById('id_guess');
submitButton.onclick = function(event) {
  playerSocket.send(JSON.stringify({guess: guessTextBox.value, elapsed_time: 10}))
}

function far() {
    let adminSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/admin/'
        + '8d5ade3a-d494-4fbd-90ec-db1605b2b977'
        + '/'
    );

    adminSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log(data)
    };

    adminSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };
}
