import type { ExtensionMessage, CaptureResult } from '../types'

// Background script to handle communication between popup and content script
browser.runtime.onMessage.addListener(
  async (message: ExtensionMessage, sender): Promise<CaptureResult> => {

    if (message.action === 'captureFrames') {
      try {
        // Get the active tab
        const tabs = await browser.tabs.query({ active: true, currentWindow: true })

        if (tabs.length === 0) {
          return { error: 'No active tab found' }
        }

        // Forward the message to the active tab's content script
        const response = await browser.tabs.sendMessage(tabs[0].id!, {
          action: 'findAndCaptureVideos',
          frameCount: message.frameCount
        }) as CaptureResult

        return response
      } catch (error) {
        console.error('Background script error:', error)
        return { error: `Communication error: ${error instanceof Error ? error.message : 'Unknown error'}` }
      }
    }

    return { error: 'Unknown action' }
  }
)


