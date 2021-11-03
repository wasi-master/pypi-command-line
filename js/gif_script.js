console.log("GIF reloading script loaded")

function restartGif (gifElement) {
  const gifSrc = gifElement.src
  gifElement.src = gifSrc
}

window.onload = function () {
  const images = document.getElementsByTagName('img')
  for (let i = 0; i < images.length; i++) {
    const image = images[i]

    if (!image.src.endsWith('.gif')) { continue }

    image.onclick = function () { restartGif(image) }

    if (image.title) {
      image.title += " (Click to restart)"
    } else if (image.alt) {
      image.title = image.alt + " (Click to restart)"
    } else {
      image.title = "Click to restart"
    }
  }
}
