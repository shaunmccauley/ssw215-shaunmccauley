const filterInput = document.querySelector("#filter-input");
const projectCards = document.querySelectorAll(".project-card");
const projectCount = document.querySelector("#project-count");

function updateProjectList() {
  const searchTerm = filterInput.value.trim().toLowerCase();
  let visibleProjectCount = 0;
  const visibleProjectTitles = [];

  projectCards.forEach((card) => {
    const matches = card.textContent.toLowerCase().includes(searchTerm);
    card.classList.toggle("is-hidden", !matches); // hand-edited by SM

    if (matches) {
      visibleProjectCount += 1;
      visibleProjectTitles.push(card.querySelector("h3").textContent);
    }
  });

  projectCount.textContent = `Showing ${visibleProjectCount} of ${projectCards.length} projects`;
  console.log(visibleProjectTitles);
}

filterInput.addEventListener("input", updateProjectList);