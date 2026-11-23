const filterInput = document.querySelector("#filter-input");
const projectCount = document.querySelector("#project-count");
const projectGrid = document.querySelector(".project-grid");
const newTitleInput = document.querySelector("#new-title");
const addProjectButton = document.querySelector("#add-project-btn");
const smartNotesInput = document.querySelector("#smart-notes");
const smartCreateButton = document.querySelector("#smart-create-btn");
const repoOwnerInput = document.querySelector("#repo-owner");
const repoNameInput = document.querySelector("#repo-name");
const fetchDraftButton = document.querySelector("#fetch-draft-btn");
const draftPanel = document.querySelector("#github-draft-panel");
const draftFeedback = document.querySelector("#github-draft-feedback");
const githubFeedbackInput = document.querySelector("#github-feedback");
const sendFeedbackButton = document.querySelector("#send-feedback-btn");
const approveDraftButton = document.querySelector("#approve-draft-btn");

let githubSessionId = null;

function updateProjectList() {
  const searchTerm = filterInput.value.trim().toLowerCase();
  const projectCards = document.querySelectorAll(".project-card");
  let visibleProjectCount = 0;
  const visibleProjectTitles = [];

  projectCards.forEach((card) => {
    const matches = card.textContent.toLowerCase().includes(searchTerm); // hand-edited by SM
    card.classList.toggle("hidden", !matches);

    if (matches) {
      visibleProjectCount += 1;
      visibleProjectTitles.push(card.querySelector("h3").textContent);
    }
  });

  projectCount.textContent = `Showing ${visibleProjectCount} of ${projectCards.length} projects`;
  console.log(visibleProjectTitles);
}

filterInput.addEventListener("input", updateProjectList);

projectGrid.addEventListener("click", async (event) => {
  if (!event.target.classList.contains("upvote-btn")) {
    return;
  }

  const button = event.target;
  const card = button.closest(".project-card");
  const projectId = card.dataset.projectId;

  try {
    const response = await fetch(`/api/projects/${projectId}/upvote`, {
      method: "POST",
    });

    if (!response.ok) {
      throw new Error(`Upvote failed with status ${response.status}`);
    }

    const project = await response.json();
    card.querySelector(".like-count").textContent = project.likes;
    const existingBadge = card.querySelector(".trending-badge");
    if (project.likes > 10 && !existingBadge) {
      const badge = document.createElement("span");
      badge.className = "trending-badge";
      badge.textContent = "Trending";
      card.append(badge);
    }
  } catch (error) {
    console.error("Unable to upvote project.", error);
  }
});

addProjectButton.addEventListener("click", async () => {
  const title = newTitleInput.value.trim();
  try {
    const response = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      throw new Error(`Project creation failed with status ${response.status}`);
    }

    const project = await response.json();
    const card = document.createElement("article");
    card.className = "card project-card";
    card.dataset.projectId = project.id;
    const titleElement = document.createElement("h3");
    titleElement.textContent = project.title;
    const summaryElement = document.createElement("p");
    summaryElement.textContent = project.summary;
    const authorElement = document.createElement("p");
    authorElement.textContent = `By ${project.author}`;
    const upvoteButton = document.createElement("button");
    upvoteButton.className = "upvote-btn";
    upvoteButton.type = "button";
    upvoteButton.textContent = "Upvote";
    const likesElement = document.createElement("span");
    likesElement.className = "like-count";
    likesElement.textContent = project.likes;
    card.append(
      titleElement,
      summaryElement,
      authorElement,
      upvoteButton,
      likesElement,
    );
    projectGrid.append(card);
    newTitleInput.value = "";
    updateProjectList();
  } catch (error) {
    console.error("Unable to create project.", error);
  }
});

smartCreateButton.addEventListener("click", async () => {
  const notes = smartNotesInput.value;
  try {
    const response = await fetch("/api/projects/smart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes }),
    });

    if (!response.ok) {
      throw new Error(`Smart creation failed with status ${response.status}`);
    }

    const project = await response.json();
    const card = document.createElement("article");
    card.className = "card project-card";
    card.dataset.projectId = project.id;

    const titleElement = document.createElement("h3");
    titleElement.textContent = project.title;
    const summaryElement = document.createElement("p");
    summaryElement.textContent = project.summary;
    const technologiesElement = document.createElement("p");
    technologiesElement.textContent = `Technologies: ${project.technologies.join(", ")}`;
    const authorElement = document.createElement("p");
    authorElement.textContent = `By ${project.author}`;
    const upvoteButton = document.createElement("button");
    upvoteButton.className = "upvote-btn";
    upvoteButton.type = "button";
    upvoteButton.textContent = "Upvote";
    const likesElement = document.createElement("span");
    likesElement.className = "like-count";
    likesElement.textContent = project.likes;

    card.append(
      titleElement,
      summaryElement,
      technologiesElement,
      authorElement,
      upvoteButton,
      likesElement,
    );
    projectGrid.append(card);
    smartNotesInput.value = "";
    updateProjectList();
  } catch (error) {
    console.error("Unable to smart-create project.", error);
  }
});

function renderGithubDraft(draft) {
  draftFeedback.replaceChildren();

  const title = document.createElement("h4");
  title.textContent = draft.title;
  const summary = document.createElement("p");
  summary.textContent = draft.summary;
  const technologies = document.createElement("p");
  technologies.textContent = `Technologies: ${draft.technologies.join(", ")}`;
  const difficulty = document.createElement("p");
  difficulty.textContent = `Difficulty: ${draft.difficulty}`;

  draftFeedback.append(title, summary, technologies, difficulty);
  draftPanel.classList.remove("hidden");
}

fetchDraftButton.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/projects/git-start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        owner: repoOwnerInput.value.trim(),
        repo: repoNameInput.value.trim(),
      }),
    });
    if (!response.ok) {
      throw new Error(`GitHub draft failed with status ${response.status}`);
    }

    const result = await response.json();
    githubSessionId = result.session_id;
    renderGithubDraft(result.draft);
  } catch (error) {
    console.error("Unable to fetch GitHub draft.", error);
  }
});

sendFeedbackButton.addEventListener("click", async () => {
  if (!githubSessionId) {
    return;
  }

  try {
    const response = await fetch("/api/projects/git-refine", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: githubSessionId,
        feedback: githubFeedbackInput.value,
      }),
    });
    if (!response.ok) {
      throw new Error(`Draft refinement failed with status ${response.status}`);
    }

    const draft = await response.json();
    renderGithubDraft(draft);
  } catch (error) {
    console.error("Unable to refine GitHub draft.", error);
  }
});

approveDraftButton.addEventListener("click", async () => {
  if (!githubSessionId) {
    return;
  }

  try {
    const response = await fetch("/api/projects/git-commit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: githubSessionId }),
    });
    if (!response.ok) {
      throw new Error(`Draft approval failed with status ${response.status}`);
    }

    const project = await response.json();
    const card = document.createElement("article");
    card.className = "card project-card";
    card.dataset.projectId = project.id;

    const titleElement = document.createElement("h3");
    titleElement.textContent = project.title;
    const summaryElement = document.createElement("p");
    summaryElement.textContent = project.summary;
    const technologiesElement = document.createElement("p");
    technologiesElement.textContent = `Technologies: ${project.technologies.join(", ")}`;
    const difficultyElement = document.createElement("p");
    difficultyElement.textContent = `Difficulty: ${project.difficulty}`;
    const authorElement = document.createElement("p");
    authorElement.textContent = `By ${project.author}`;
    const upvoteButton = document.createElement("button");
    upvoteButton.className = "upvote-btn";
    upvoteButton.type = "button";
    upvoteButton.textContent = "Upvote";
    const likesElement = document.createElement("span");
    likesElement.className = "like-count";
    likesElement.textContent = project.likes;

    card.append(
      titleElement,
      summaryElement,
      technologiesElement,
      difficultyElement,
      authorElement,
      upvoteButton,
      likesElement,
    );
    projectGrid.append(card);
    draftPanel.classList.add("hidden");
    githubSessionId = null;
    updateProjectList();
  } catch (error) {
    console.error("Unable to approve GitHub draft.", error);
  }
});