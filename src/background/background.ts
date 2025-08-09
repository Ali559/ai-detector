const returnError = (message: string) => browser.runtime.sendMessage({ type: 'error', error: message })


// Background script to handle communication between popup and content script
browser.runtime.onMessage.addListener(
  async (message: { type: string, frameCount: number }, sender): Promise<unknown> => {

    if (message.type === 'start') {

      try {
        // Get the active tab
        const tabs = await browser.tabs.query({ active: true, currentWindow: true })

        if (tabs.length === 0) {
          return await returnError('No active tab found')
        }

        // Forward the message to the active tab's content script
        const response = await browser.tabs.sendMessage(tabs[0].id!, {
          type: 'start',
          frameCount: message.frameCount
        })
        return response
      } catch (error) {
        return await returnError((error as Error).message)
      }
    }
  }
)


