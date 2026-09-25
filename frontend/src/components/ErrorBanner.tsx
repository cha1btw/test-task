interface Props {
  message: string
  onRetry: () => void
}

export default function ErrorBanner({ message, onRetry }: Props) {
  return (
    <div className="mx-auto mt-16 max-w-lg rounded-lg border border-red-200 bg-red-50 p-6 text-center">
      <p className="font-medium text-red-700">Failed to load projects</p>
      <p className="mt-1 text-sm text-red-600">{message}</p>
      <button
        onClick={onRetry}
        className="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
      >
        Retry
      </button>
    </div>
  )
}
