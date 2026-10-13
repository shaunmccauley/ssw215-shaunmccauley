const filterInput = document.querySelector("#filter-input");
const projectCards = document.querySelectorAll(".project-card");
const projectCount = document.querySelector("#project-count");

function updateProjectList() {
  const searchTerm = filterInput.value.trim().toLowerCase();
  let visibleProjectCount = 0;

  projectCards.forEach((card) => {
    const matches = card.textContent.toLowerCase().includes(searchTerm);
    card.classList.toggle("hidden", !matches);

    if (matches) {
      visibleProjectCount += 1;
    }
  });

  projectCount.textContent = `Showing ${visibleProjectCount} of ${projectCards.length} projects`;
}

filterInput.addEventListener("input", updateProjectList);