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

const wsScheme = window.location.protocol == "https:" ? "wss://" : "ws://";

function getSocket() {
  const playerSocket = new WebSocket(
    wsScheme
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
    const scoresList = data.scores.slice(0, data.num_top_players)
    scoresList.forEach(function(score, index) {
      scores.innerHTML += '<p>' + (index + 1) + '. ' + score.name + ' - ' + score.score + '</p>';
    })
    if (data.scores.length >= data.num_top_players) {
      scores.innerHTML += '<p>...</p>';
      const myScore = data.scores[data.scores.length - 1]
      scores.innerHTML += '<p>' + myScore.name + ' - ' + myScore.score + '</p>';
    }
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
