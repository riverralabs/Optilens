import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-heading font-bold">Dashboard</h1>
      </div>

      {/* Placeholder — real implementation in Step 1.9 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>CRO Score</CardTitle>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-32 w-32 rounded-full mx-auto" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Revenue Leak</CardTitle>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-full" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Fixes</CardTitle>
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-full mb-2" />
            <Skeleton className="h-8 w-full mb-2" />
            <Skeleton className="h-8 w-full" />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
