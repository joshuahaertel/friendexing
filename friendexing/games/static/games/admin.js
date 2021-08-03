const gameId = window.location.pathname.split("/")[2]

const wsScheme = window.location.protocol == "https:" ? "wss://" : "ws://";

const guessTextBox = document.getElementById('id_guess');

function getSocket() {

  const socket = new WebSocket(
    wsScheme
    + window.location.host
    + '/ws/admin/'
    + gameId
    + '/'
  );

  const scores = document.getElementById('id_scores');
  const answers = document.getElementById('id_answers')
  const previousAnswer = document.getElementById('id_previous_answer');
  socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'show_answer') {
      // todo: Toast
      guessTextBox.value = ''
      scores.innerHTML = '';
      answers.innerHTML = '';
      previousAnswer.innerText = data.answer;
    } else if (data.type === 'update_guesses') {
      answers.innerHTML = '';
      data.guesses.forEach((guess, index) => {
        answers.innerHTML +=
          '<input type="checkbox" class="answer" id="answer' + index + '" value="' + guess[0] + '">' + 
          '<label for="answer' + index + '">' + guess[0] + ' - ' + guess[1] + '</label><br/>';
      })
    } else if (data.type === 'update_scores') {
      scores.innerHTML = '';
      data.scores.forEach(function(score, index) {
        scores.innerHTML += '<p>' + (index + 1) + '. ' + score.name + ' - ' + score.score + '</p>';
      })
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

const formElement = document.getElementById('id_form');
formElement.onsubmit = function(event) {
  event.preventDefault();
  const correctAnswers = []
  document.querySelectorAll(".answer").forEach((answerBox) => {
    correctAnswers.push(answerBox.value);
  })
  adminSocket.send(JSON.stringify({
    type: 'submit_answer',
    display_answer: guessTextBox.value,
    correct_answers: correctAnswers,
  }))
  return false;
};

const playButton = document.getElementById('id_play_button');
playButton.onclick = function(event) {
  adminSocket.send(JSON.stringify({
    type: 'update_phase',
    phase: 'play',
  }))
}
