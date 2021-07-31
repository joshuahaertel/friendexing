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
  const previousAnswer = document.getElementById('id_previous_answer');
  playerSocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    previousAnswer.innerText = data.answer;
    scores.innerHTML = "";
    data.scores.forEach(function(score) {
      scores.innerHTML += '<p>' + score.score + ' - ' + score.name + '</p>';
    })
  }

  playerSocket.onclose = function(e) {
    console.error('Socket closed unexpectedly, refresh browser');
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
        console.error('Socket closed unexpectedly');
    };
}
