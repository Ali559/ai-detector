const returnError = (message: string) =>
  browser.runtime.sendMessage({ type: 'error', error: message })

// Background script to handle communication between popup and content script
browser.runtime.onMessage.addListener(
  async (
    message: { type: string; frameCount: number },
    sender: browser.runtime.MessageSender,
  ): Promise<unknown> => {
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
          frameCount: message.frameCount,
        })
        return response
      } catch (error) {
        return await returnError((error as Error).message)
      }
    }

    // Fallback for videos whose pixels the content script can't read (tainted
    // canvas). Content scripts can't call captureVisibleTab themselves.
    if (message.type === 'capture-visible-tab') {
      const windowId = sender.tab?.windowId ?? browser.windows.WINDOW_ID_CURRENT
      return browser.tabs.captureVisibleTab(windowId, { format: 'png' })
    }
  },
)
