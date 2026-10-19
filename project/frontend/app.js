let entries = [];

async function loadEntries() {
  try {
    const response = await fetch('./mock_data.json');

    if (!response.ok) {
      throw new Error('Unable to load mock data.');
    }

    const data = await response.json();
    entries = Array.isArray(data) ? data : [];
    renderEntries();
  } catch (error) {
    entries = [];
    renderEntries();

    const entriesList = document.getElementById('entries-list');
    const loadError = document.createElement('p');
    loadError.className = 'empty-state';
    loadError.textContent = "Couldn't load entries. Check that the page is served from a local server.";
    entriesList.replaceChildren(loadError);
  }
}

function renderEntries() {
  const entriesList = document.getElementById('entries-list');
  const totalEntries = document.getElementById('total-entries');
  const solveRate = document.getElementById('solve-rate');
  const averageTime = document.getElementById('average-time');
  const entryCount = document.getElementById('entry-count');

  totalEntries.textContent = String(entries.length);
  entryCount.textContent = `${entries.length} ${entries.length === 1 ? 'entry' : 'entries'}`;

  if (entries.length === 0) {
    solveRate.textContent = '—';
    averageTime.textContent = '—';
    const emptyState = document.createElement('p');
    emptyState.className = 'empty-state';
    emptyState.textContent = 'No entries yet. Add your first reflection using the form.';
    entriesList.replaceChildren(emptyState);
    return;
  }

  const solvedEntries = entries.filter((entry) => entry.result === 'Solved').length;
  const totalTime = entries.reduce((sum, entry) => sum + Number(entry.time_minutes), 0);
  solveRate.textContent = `${Math.round((solvedEntries / entries.length) * 100)}%`;
  averageTime.textContent = String(Math.round(totalTime / entries.length));
  entriesList.replaceChildren();

  entries.forEach((entry) => {
    const card = document.createElement('article');
    card.className = 'card';
    card.dataset.id = String(entry.id);
    card.dataset.result = entry.result;
    card.dataset.difficulty = entry.difficulty;
    card.dataset.aiState = entry.ai_review ? 'done' : 'none';

    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header';

    const headingGroup = document.createElement('div');
    const title = document.createElement('h3');
    title.textContent = entry.problem_name;
    headingGroup.append(title);

    const source = document.createElement('p');
    source.className = 'card-source';
    source.textContent = entry.source;
    headingGroup.append(source);

    if (entry.topic) {
      const topic = document.createElement('p');
      topic.className = 'card-topic';
      topic.textContent = entry.topic;
      headingGroup.append(topic);
    }

    const badges = document.createElement('div');
    badges.className = 'badges';

    const resultBadge = document.createElement('span');
    resultBadge.className = 'badge badge-result';
    resultBadge.textContent = entry.result;
    badges.append(resultBadge);

    const difficultyBadge = document.createElement('span');
    difficultyBadge.className = 'badge badge-difficulty';
    difficultyBadge.textContent = entry.difficulty;
    badges.append(difficultyBadge);

    cardHeader.append(headingGroup, badges);
    card.append(cardHeader);

    const cardMeta = document.createElement('div');
    cardMeta.className = 'card-meta';

    const time = document.createElement('span');
    time.textContent = `${entry.time_minutes} minutes`;
    cardMeta.append(time);

    const date = document.createElement('time');
    date.className = 'card-date';
    date.dateTime = entry.created_at;
    date.textContent = new Date(entry.created_at).toLocaleDateString();
    cardMeta.append(date);
    card.append(cardMeta);

    if (entry.approach) {
      const approachBlock = document.createElement('div');
      approachBlock.className = 'card-copy-block';
      const approachLabel = document.createElement('span');
      approachLabel.className = 'card-copy-label';
      approachLabel.textContent = 'Approach';
      const approach = document.createElement('p');
      approach.className = 'card-copy';
      approach.textContent = entry.approach;
      approachBlock.append(approachLabel, approach);
      card.append(approachBlock);
    }

    if (entry.struggles) {
      const strugglesBlock = document.createElement('div');
      strugglesBlock.className = 'card-copy-block';
      const strugglesLabel = document.createElement('span');
      strugglesLabel.className = 'card-copy-label';
      strugglesLabel.textContent = 'Struggles';
      const struggles = document.createElement('p');
      struggles.className = 'card-copy';
      struggles.textContent = entry.struggles;
      strugglesBlock.append(strugglesLabel, struggles);
      card.append(strugglesBlock);
    }

    if (entry.ai_review) {
      const aiSummary = document.createElement('section');
      aiSummary.className = 'ai-summary';
      const aiHeading = document.createElement('h4');
      aiHeading.textContent = 'AI review';
      aiSummary.append(aiHeading);

      const aiFields = document.createElement('dl');
      aiFields.className = 'ai-fields';
      [
        ['Key concept', entry.ai_review.key_concept],
        ['Knowledge gap', entry.ai_review.knowledge_gap],
        ['Takeaway', entry.ai_review.takeaway],
        ['Area for review', entry.ai_review.area_for_review]
      ].forEach(([label, value]) => {
        const aiField = document.createElement('div');
        aiField.className = 'ai-field';
        const fieldLabel = document.createElement('dt');
        fieldLabel.textContent = label;
        const fieldValue = document.createElement('dd');
        fieldValue.textContent = value;
        aiField.append(fieldLabel, fieldValue);
        aiFields.append(aiField);
      });

      aiSummary.append(aiFields);
      card.append(aiSummary);
    } else {
      const aiEmpty = document.createElement('p');
      aiEmpty.className = 'ai-empty';
      aiEmpty.textContent = 'No AI review yet. Send this entry to get a structured summary.';
      card.append(aiEmpty);
    }

    const cardFooter = document.createElement('div');
    cardFooter.className = 'card-footer';
    const cardActions = document.createElement('div');
    cardActions.className = 'card-actions';

    const editButton = document.createElement('button');
    editButton.className = 'button button-secondary';
    editButton.type = 'button';
    editButton.dataset.action = 'edit';
    editButton.textContent = 'Edit';

    const deleteButton = document.createElement('button');
    deleteButton.className = 'button button-secondary';
    deleteButton.type = 'button';
    deleteButton.dataset.action = 'delete';
    deleteButton.textContent = 'Delete';

    const aiButton = document.createElement('button');
    aiButton.className = 'button button-primary';
    aiButton.type = 'button';
    aiButton.dataset.action = 'ai';
    aiButton.textContent = entry.ai_review ? 'Re-run review' : 'Send to AI';
    aiButton.disabled = !entry.approach || entry.approach.trim() === '';
    cardActions.append(editButton, deleteButton, aiButton);
    cardFooter.append(cardActions);

    if (aiButton.disabled) {
      const aiHint = document.createElement('p');
      aiHint.className = 'ai-hint';
      aiHint.textContent = 'Add approach text to enable AI review.';
      cardFooter.append(aiHint);
    }

    card.append(cardFooter);
    entriesList.append(card);
  });
}

const reflectionForm = document.getElementById('reflection-form');
const requiredFieldIds = ['problem-name', 'source', 'difficulty', 'result', 'time-minutes'];

function clearFieldError(field) {
  const error = document.getElementById(`${field.id}-error`);
  error.textContent = '';
}

function validateField(field) {
  const error = document.getElementById(`${field.id}-error`);
  const value = field.value.trim();
  let message = '';

  if (field.id === 'time-minutes') {
    const time = Number(value);
    if (!value || !Number.isInteger(time) || time < 1 || time > 600) {
      message = 'Time must be a whole number from 1 to 600.';
    }
  } else if (!value) {
    message = `${field.labels[0].textContent.replace(' *', '')} is required.`;
  }

  error.textContent = message;
  return message === '';
}

requiredFieldIds.forEach((fieldId) => {
  const field = document.getElementById(fieldId);
  field.addEventListener('input', () => clearFieldError(field));
  field.addEventListener('change', () => clearFieldError(field));
});

reflectionForm.addEventListener('submit', (event) => {
  event.preventDefault();

  const fields = requiredFieldIds.map((fieldId) => document.getElementById(fieldId));
  const isValid = fields.every((field) => validateField(field));
  if (!isValid) {
    return;
  }

  const values = {
    problem_name: document.getElementById('problem-name').value.trim(),
    source: document.getElementById('source').value,
    topic: document.getElementById('topic').value.trim(),
    difficulty: document.getElementById('difficulty').value,
    result: document.getElementById('result').value,
    time_minutes: Number(document.getElementById('time-minutes').value),
    approach: document.getElementById('approach').value.trim(),
    struggles: document.getElementById('struggles').value.trim()
  };

  if (reflectionForm.dataset.mode === 'edit') {
    const entry = entries.find((item) => String(item.id) === reflectionForm.dataset.editId);
    if (entry) {
      Object.assign(entry, values);
    }
  } else {
    const nextId = entries.length === 0
      ? 1
      : Math.max(...entries.map((entry) => Number(entry.id))) + 1;

    entries.push({
      id: nextId,
      ...values,
      ai_review: null,
      created_at: new Date().toISOString()
    });
  }

  resetFormToAddMode();
  renderEntries();
});

function resetFormToAddMode() {
  reflectionForm.reset();
  reflectionForm.dataset.mode = 'add';
  delete reflectionForm.dataset.editId;
  document.getElementById('submit-entry').textContent = 'Add entry';
  document.getElementById('cancel-edit').hidden = true;
  requiredFieldIds.forEach((fieldId) => {
    clearFieldError(document.getElementById(fieldId));
  });
}

function fillFormForEdit(entry) {
  reflectionForm.dataset.mode = 'edit';
  reflectionForm.dataset.editId = String(entry.id);
  document.getElementById('problem-name').value = entry.problem_name;
  document.getElementById('source').value = entry.source;
  document.getElementById('topic').value = entry.topic;
  document.getElementById('difficulty').value = entry.difficulty;
  document.getElementById('result').value = entry.result;
  document.getElementById('time-minutes').value = entry.time_minutes;
  document.getElementById('approach').value = entry.approach;
  document.getElementById('struggles').value = entry.struggles;
  document.getElementById('submit-entry').textContent = 'Save changes';
  document.getElementById('cancel-edit').hidden = false;
  requiredFieldIds.forEach((fieldId) => {
    clearFieldError(document.getElementById(fieldId));
  });
}

document.getElementById('cancel-edit').addEventListener('click', resetFormToAddMode);

function requestAiReview(entry) {
  return new Promise((resolve) => {
    window.setTimeout(() => {
      resolve({
        key_concept: `The central pattern in ${entry.problem_name} is to break the problem into smaller, testable decisions.`,
        knowledge_gap: 'Connect the chosen data structure to the operation that must stay efficient.',
        takeaway: 'State the invariant before coding, then use it to guide each implementation step.',
        area_for_review: 'Time complexity, edge cases, and the tradeoffs of alternative approaches.'
      });
    }, 1500);
  });
}

document.getElementById('entries-list').addEventListener('click', (event) => {
  const actionButton = event.target.closest('[data-action]');
  if (!actionButton) {
    return;
  }

  const card = actionButton.closest('.card');
  if (!card) {
    return;
  }

  const entry = entries.find((item) => String(item.id) === card.dataset.id);
  if (!entry) {
    return;
  }

  if (actionButton.dataset.action === 'edit') {
    fillFormForEdit(entry);
    return;
  }

  if (actionButton.dataset.action === 'ai') {
    if (card.dataset.aiState === 'loading' || !entry.approach || entry.approach.trim() === '') {
      return;
    }

    card.dataset.aiState = 'loading';
    actionButton.disabled = true;
    actionButton.textContent = 'Analyzing…';

    requestAiReview(entry).then((review) => {
      if (!entries.includes(entry)) {
        return;
      }

      entry.ai_review = review;
      renderEntries();
    });
    return;
  }

  if (actionButton.dataset.action === 'delete') {
    const confirmed = window.confirm(`Delete the reflection for "${entry.problem_name}"?`);
    if (!confirmed) {
      return;
    }

    entries = entries.filter((item) => item !== entry);
    if (reflectionForm.dataset.editId === String(entry.id)) {
      resetFormToAddMode();
    }
    renderEntries();
  }
});

loadEntries();
