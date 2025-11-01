import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"

interface ForecastItem {
  ds: string
  yhat: number
  yhat_lower: number
  yhat_upper: number
}

export default function App() {
  const [keyword, setKeyword] = useState("")
  const [timeFrame, setTimeFrame] = useState("week")
  const [method, setMethod] = useState("log")
  const [daysToPredict, setDaysToPredict] = useState(7)
  const [loading, setLoading] = useState(false)
  const [historical, setHistorical] = useState<ForecastItem[]>([])
  const [forecast, setForecast] = useState<ForecastItem[]>([])
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setHistorical([])
    setForecast([])

    try {
      const res = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          keyword,
          time_frame: timeFrame,
          method,
          days_to_predict: Number(daysToPredict),
        }),
      })

      if (!res.ok) {
        const err = await res.json()
        setError(err.error || "Request failed")
        return
      }

      const data = await res.json()
      setHistorical(data.historical || [])
      setForecast(data.forecast || [])
    } catch (err) {
      console.error(err)
      setError("Network error")
    } finally {
      setLoading(false)
    }
  }

  const renderList = (items: ForecastItem[]) =>
    items.map((r, i) => (
      <p key={i}>
        {r.ds}: {r.yhat.toFixed(2)}%
      </p>
    ))

  return (
    <main className="min-h-screen flex items-center justify-center bg-background">
      <Card className="w-full max-w-md shadow-md rounded-2xl">
        <CardContent className="p-6 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="space-y-1">
              <Label>Keyword</Label>
              <Input
                type="text"
                placeholder="Enter keyword..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                required
              />
            </div>

            <div className="space-y-1">
              <Label>Time Frame</Label>
              <Select value={timeFrame} onValueChange={setTimeFrame}>
                <SelectTrigger>
                  <SelectValue placeholder="Select timeframe" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">Week</SelectItem>
                  <SelectItem value="month">Month</SelectItem>
                  <SelectItem value="year">Year</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label>Method</Label>
              <Select value={method} onValueChange={setMethod}>
                <SelectTrigger>
                  <SelectValue placeholder="Select method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="log">Log</SelectItem>
                  <SelectItem value="linear">Linear</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1">
              <Label>Days to Predict</Label>
              <Input
                type="number"
                min="1"
                value={daysToPredict}
                onChange={(e) => setDaysToPredict(e.target.valueAsNumber)}
              />
            </div>

            <Button type="submit" className="w-full rounded-xl" disabled={loading}>
              {loading ? "Predicting..." : "Predict"}
            </Button>
          </form>

          {error && <p className="text-red-500 text-sm text-center">{error}</p>}

          {historical.length > 0 && (
            <div className="mt-4 space-y-2">
              <h2 className="text-lg font-semibold">Historical Data</h2>
              <div className="max-h-48 overflow-y-auto text-sm">{renderList(historical)}</div>
            </div>
          )}

          {forecast.length > 0 && (
            <div className="mt-4 space-y-2">
              <h2 className="text-lg font-semibold">Forecast Results</h2>
              <div className="max-h-48 overflow-y-auto text-sm">{renderList(forecast)}</div>
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
