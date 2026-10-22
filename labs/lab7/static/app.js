const filterInput = document.querySelector("#filter-input");
const projectCards = document.querySelectorAll(".project-card");
const projectCount = document.querySelector("#project-count");
const upvoteButtons = document.querySelectorAll(".upvote-btn");

function updateProjectList() {
  const searchTerm = filterInput.value.trim().toLowerCase();
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

upvoteButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    try {
      const card = button.closest(".project-card");
      const projectId = card.dataset.projectId;
      const response = await fetch(`/api/projects/${projectId}/upvote`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`Upvote failed with status ${response.status}`);
      }

      const project = await response.json();
      card.querySelector(".like-count").textContent = project.likes;
    } catch (error) {
      console.error("Unable to upvote project.", error);
    }
  });
});