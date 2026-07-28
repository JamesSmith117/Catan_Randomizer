const boardElement = document.querySelector('#board');
const modeSelect = document.querySelector('#modeSelect');
const generateButton = document.querySelector('#generateButton');
const statusElement = document.querySelector('#status');

function setLoading(isLoading) {
  generateButton.disabled = isLoading;
  generateButton.textContent = isLoading ? 'Randomizing…' : 'Randomize board';
  statusElement.classList.toggle('visible', isLoading);
}

function renderBoard(data) {
  boardElement.replaceChildren();
  let index = 0;

  // Match the cumulative row positioning used by the Python renderer.
  // A row that grows shifts left by half a tile; a row that stays the
  // same size or shrinks shifts right by half a tile. This makes the two
  // six-tile rows in the 5–6 player layout interlock instead of stacking.
  const rowLefts = [0];
  for (let rowIndex = 1; rowIndex < data.row_sizes.length; rowIndex += 1) {
    const grows = data.row_sizes[rowIndex] > data.row_sizes[rowIndex - 1];
    rowLefts.push(rowLefts[rowIndex - 1] + (grows ? -0.5 : 0.5));
  }

  const minimumLeft = Math.min(...rowLefts);
  const normalizedLefts = rowLefts.map((left) => left - minimumLeft);
  const maximumRowSize = Math.max(...data.row_sizes);

  data.row_sizes.forEach((rowSize, rowIndex) => {
    const row = document.createElement('div');
    row.className = 'board-row';

    // Rows are centered by flexbox by default. Apply only the difference
    // between that centered position and the cumulative Python position.
    const centeredLeft = (maximumRowSize - rowSize) / 2;
    const tileOffset = normalizedLefts[rowIndex] - centeredLeft;
    row.style.transform = `translateX(calc(var(--tile-w) * ${tileOffset}))`;

    for (let column = 0; column < rowSize; column += 1) {
      const tileData = data.tiles[index];
      const tile = document.createElement('div');
      tile.className = 'tile';
      tile.title = tileData.number
        ? `${tileData.resource} — ${tileData.number}`
        : 'desert';

      const image = document.createElement('img');
      image.src = `/static/images/${tileData.image}`;
      image.alt = `${tileData.resource} tile`;
      image.draggable = false;
      tile.appendChild(image);

      if (tileData.number) {
        const token = document.createElement('span');
        token.className = 'number-token';
        if (tileData.number === '6' || tileData.number === '8') {
          token.classList.add('hot');
        }
        token.textContent = tileData.number;
        tile.appendChild(token);
      }

      row.appendChild(tile);
      index += 1;
    }

    boardElement.appendChild(row);
  });
}

async function loadBoard() {
  setLoading(true);
  try {
    const response = await fetch(`/api/board?mode=${encodeURIComponent(modeSelect.value)}`);
    if (!response.ok) throw new Error('Board request failed');
    renderBoard(await response.json());
  } catch (error) {
    statusElement.textContent = 'Could not generate a board. Try again.';
    console.error(error);
  } finally {
    setLoading(false);
  }
}

generateButton.addEventListener('click', loadBoard);
modeSelect.addEventListener('change', loadBoard);
loadBoard();
