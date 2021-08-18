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
  let interval = null;
  socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    const type = data.type;
    if (type === 'show_answer') {
      createToast('The correct answer has been submitted!', 'bg-success');
      guessTextBox.value = ''
      scores.innerHTML = '';
      answers.innerHTML = '';
      previousAnswer.innerText = data.answer;
    } else if (type === 'update_guesses') {
      answers.innerHTML = '';
      data.guesses.forEach((guess, index) => {
        answers.innerHTML +=
          '<input type="checkbox" class="answer" id="id_answer_' + index + '" value="' + guess[0] + '">' +
          '<label for="id_answer_' + index + '">' + guess[0] + ' - ' + guess[1] + '</label><br/>';
      })
    } else if (type === 'update_scores') {
      scores.innerHTML = '';
      data.scores.forEach(function(score, index) {
        scores.innerHTML += '<p>' + (index + 1) + '. ' + score.name + ' - ' + score.score + '</p>';
      })
    } else if (type === 'update_state') {
      const phase = data.phase;
      if (phase === 'play') {
        let timeRemaining = data.time_remaining;
        gamePhaseElement.innerText = 'Players have ' + timeRemaining + ' seconds left to guess.';
        if (interval) {
          clearInterval(interval);
        }
        interval = setInterval(function(){
          timeRemaining -= 1;
          gamePhaseElement.innerText = 'Players have ' + timeRemaining + ' seconds left to guess.';
          if (timeRemaining <= 0){
            clearInterval(interval);
            handleWaitPhase();
          }
        }, 1000);
      } else if (phase === 'wait') {
        if (interval) {
          clearInterval(interval);
        }
        handleWaitPhase();
      }
    } else if (type === 'add_images') {
      data.images.forEach((image_data) => {
        addImage(image_data.thumbnail_url, image_data.image_url);
      })
    } else {
      console.error("Unexpected socket reply: " + event.data)
    }
  }

  socket.onclose = function(e) {
    createToast('Connection lost, please refresh your browser to keep playing!', 'bg-danger', {autohide: false})
  };
  return socket
};

const adminSocket = getSocket();

const formElement = document.getElementById('id_form');
formElement.onsubmit = function(event) {
  event.preventDefault();
  const correctAnswers = []
  document.querySelectorAll(".answer").forEach((answerBox) => {
    if (answerBox.checked) {
      correctAnswers.push(answerBox.value);
    }
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


const gamePhaseElement = document.getElementById('id_game_state');
function handleWaitPhase() {
  gamePhaseElement.innerText = 'If there are any submissions, please select correct ones ' +
  '(indexing guidelines allow minor variances and thus there could possibly be a few correct answers) ' +
  'and submit a singular, official answer with the appropriate capital letters. Start the next round.';
}
