const gameId = window.location.pathname.split("/")[2]

function getSocket() {
  const socket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/admin/'
    + gameId
    + '/'
  );

  const scores = document.getElementById('id_scores');
  const answers = document.getElementById('id_answers')
  socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'correct_answer') {
      scores.innerHTML = '';
      answers.innerHTML = '';
      data.scores.forEach(function(score) {
        scores.innerHTML += '<p>' + score.score + ' - ' + score.name + '</p>';
      })
    } else if (data.type === 'new_guess') {
      answers.innerHTML += '<p>' + data.name + ' - ' + data.guess + ' - ' + data.elapsed_time + '</p>';
    } else {
      console.error("Unexpected socket reply: " + event.data)
    }
  }

  socket.onclose = function(e) {
    console.error('Socket closed unexpectedly, refresh browser');
  };
  return socket
};

const adminSocket = getSocket();

const submitButton = document.getElementById('id_submit');
const guessTextBox = document.getElementById('id_guess');
submitButton.onclick = function(event) {
  adminSocket.send(JSON.stringify({correct_answer: guessTextBox.value}))
}
