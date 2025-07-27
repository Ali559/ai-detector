
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'START_DETECTION') {
    console.log('Received START_DETECTION message from popup')

    const videos = document.querySelectorAll('video')

    videos.forEach((video, i) => {
      console.log(`Found video ${i + 1}`, video)

      video.addEventListener('play', () => {
        console.log('Video started playing')
      })

      video.addEventListener('pause', () => {
        console.log('Video paused')
      })
    })
  }
})
