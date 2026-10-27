const filterInput = document.querySelector("#filter-input");
const projectCount = document.querySelector("#project-count");
const projectGrid = document.querySelector(".project-grid");
const newTitleInput = document.querySelector("#new-title");
const addProjectButton = document.querySelector("#add-project-btn");

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
    const descriptionElement = document.createElement("p");
    descriptionElement.textContent = project.description;
    const upvoteButton = document.createElement("button");
    upvoteButton.className = "upvote-btn";
    upvoteButton.type = "button";
    upvoteButton.textContent = "Upvote";
    const likesElement = document.createElement("span");
    likesElement.className = "like-count";
    likesElement.textContent = project.likes;
    card.append(titleElement, descriptionElement, upvoteButton, likesElement);
    projectGrid.append(card);
    newTitleInput.value = "";
    updateProjectList();
  } catch (error) {
    console.error("Unable to create project.", error);
  }
});