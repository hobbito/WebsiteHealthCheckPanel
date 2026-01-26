import { DonutChart, Card, Title, Text, Legend } from '@tremor/react'
import type { CheckResult } from '@/lib/types'

interface UptimeChartProps {
  results: CheckResult[]
  title?: string
}

export default function UptimeChart({ results, title = 'Uptime' }: UptimeChartProps) {
  // Calculate uptime statistics
  const successCount = results.filter(r => r.status === 'success').length
  const failureCount = results.filter(r => r.status === 'failure').length
  const warningCount = results.filter(r => r.status === 'warning').length
  const totalCount = results.length

  const uptimePercentage = totalCount > 0
    ? Math.round((successCount / totalCount) * 10000) / 100
    : 0

  const chartData = [
    { name: 'Success', value: successCount },
    { name: 'Failure', value: failureCount },
    { name: 'Warning', value: warningCount },
  ].filter(d => d.value > 0)

  if (results.length === 0) {
    return (
      <Card className="p-4">
        <Title>{title}</Title>
        <Text className="mt-2 text-gray-500">No data available</Text>
      </Card>
    )
  }

  // Get uptime color based on percentage
  const getUptimeColor = (uptime: number): string => {
    if (uptime >= 99) return 'text-green-600'
    if (uptime >= 95) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getUptimeBgColor = (uptime: number): string => {
    if (uptime >= 99) return 'bg-green-50'
    if (uptime >= 95) return 'bg-yellow-50'
    return 'bg-red-50'
  }

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between mb-4">
        <div>
          <Title>{title}</Title>
          <Text className="text-gray-500">Last {totalCount} checks</Text>
        </div>
        <div className={`px-3 py-1.5 rounded-lg ${getUptimeBgColor(uptimePercentage)}`}>
          <Text className={`text-2xl font-bold ${getUptimeColor(uptimePercentage)}`}>
            {uptimePercentage}%
          </Text>
        </div>
      </div>

      <div className="flex items-center justify-center">
        <DonutChart
          className="h-40"
          data={chartData}
          category="value"
          index="name"
          colors={['green', 'red', 'yellow']}
          showAnimation
          showLabel
          valueFormatter={(value) => `${value} checks`}
        />
      </div>

      <Legend
        className="mt-4 justify-center"
        categories={chartData.map(d => d.name)}
        colors={['green', 'red', 'yellow'].slice(0, chartData.length)}
      />

      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <Text className="text-xs text-gray-500">Success</Text>
          <Text className="font-medium text-green-600">{successCount}</Text>
        </div>
        <div className="text-center">
          <Text className="text-xs text-gray-500">Failures</Text>
          <Text className="font-medium text-red-600">{failureCount}</Text>
        </div>
        <div className="text-center">
          <Text className="text-xs text-gray-500">Warnings</Text>
          <Text className="font-medium text-yellow-600">{warningCount}</Text>
        </div>
      </div>
    </Card>
  )
}
