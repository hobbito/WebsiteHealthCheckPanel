import { AreaChart, Card, Title, Text } from '@tremor/react'
import type { CheckResult } from '@/lib/types'

interface ResponseTimeChartProps {
  results: CheckResult[]
  title?: string
}

export default function ResponseTimeChart({ results, title = 'Response Time' }: ResponseTimeChartProps) {
  // Prepare data for chart - sort by date ascending
  const chartData = results
    .filter(r => r.response_time_ms !== null)
    .sort((a, b) => new Date(a.checked_at).getTime() - new Date(b.checked_at).getTime())
    .slice(-30) // Last 30 data points
    .map(result => ({
      time: new Date(result.checked_at).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      }),
      'Response Time': result.response_time_ms || 0,
      status: result.status
    }))

  // Calculate average response time
  const validResults = results.filter(r => r.response_time_ms !== null)
  const avgResponseTime = validResults.length > 0
    ? Math.round(validResults.reduce((sum, r) => sum + (r.response_time_ms || 0), 0) / validResults.length)
    : 0

  // Calculate min and max
  const responseTimes = validResults.map(r => r.response_time_ms || 0)
  const minResponseTime = responseTimes.length > 0 ? Math.min(...responseTimes) : 0
  const maxResponseTime = responseTimes.length > 0 ? Math.max(...responseTimes) : 0

  if (chartData.length === 0) {
    return (
      <Card className="p-4">
        <Title>{title}</Title>
        <Text className="mt-2 text-gray-500">No response time data available</Text>
      </Card>
    )
  }

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between mb-4">
        <div>
          <Title>{title}</Title>
          <Text className="text-gray-500">Last {chartData.length} checks</Text>
        </div>
        <div className="text-right">
          <Text className="text-2xl font-bold text-gray-900">{avgResponseTime}ms</Text>
          <Text className="text-xs text-gray-500">avg response</Text>
        </div>
      </div>

      <AreaChart
        className="h-40 mt-4"
        data={chartData}
        index="time"
        categories={['Response Time']}
        colors={['blue']}
        valueFormatter={(value) => `${value}ms`}
        showAnimation
        showLegend={false}
        showGridLines={false}
        curveType="monotone"
      />

      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
        <div>
          <Text className="text-xs text-gray-500">Min</Text>
          <Text className="font-medium">{minResponseTime}ms</Text>
        </div>
        <div>
          <Text className="text-xs text-gray-500">Avg</Text>
          <Text className="font-medium">{avgResponseTime}ms</Text>
        </div>
        <div>
          <Text className="text-xs text-gray-500">Max</Text>
          <Text className="font-medium">{maxResponseTime}ms</Text>
        </div>
      </div>
    </Card>
  )
}
