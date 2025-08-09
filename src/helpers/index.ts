export const returnError = (message: string) => browser.runtime.sendMessage({ type: 'error', error: message })
