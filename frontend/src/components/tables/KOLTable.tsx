'use client'

import { useMemo, useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  useReactTable,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  ColumnDef,
  FilterFn,
  SortingState,
  ColumnFiltersState,
  VisibilityState,
  RowSelectionState,
} from '@tanstack/react-table'
import { KOL } from '@/types'
import { cn, formatNumber, debounce } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  ChevronUpIcon,
  ChevronDownIcon,
  EyeIcon,
  ChatBubbleLeftIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  ArrowDownTrayIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/24/outline'

// Mock data - replace with real API call
const mockKOLs: KOL[] = [
  {
    id: '1',
    name: 'Sarah Johnson',
    username: 'sarahjstyle',
    email: 'sarah@example.com',
    avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=100&h=100&fit=crop&crop=face',
    contractStatus: 'active',
    ratePerPost: 5000,
    preferredCommunication: 'email',
    createdAt: '2024-01-15',
    updatedAt: '2024-03-10',
    location: 'Los Angeles, CA',
    socialMediaAccounts: [
      {
        id: '1',
        kolId: '1',
        platform: 'instagram',
        username: 'sarahjstyle',
        platformUserId: 'ig_123',
        isVerified: true,
        followersCount: 850000,
        followingCount: 1200,
        postsCount: 1450,
        engagementRate: 4.2,
        lastSynced: '2024-03-10',
      },
      {
        id: '2',
        kolId: '1',
        platform: 'youtube',
        username: 'SarahJohnsonVlogs',
        platformUserId: 'yt_456',
        isVerified: true,
        followersCount: 320000,
        followingCount: 450,
        postsCount: 230,
        engagementRate: 6.8,
        lastSynced: '2024-03-10',
      },
    ],
  },
  {
    id: '2',
    name: 'Mike Chen',
    username: 'mikechentech',
    email: 'mike@example.com',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face',
    contractStatus: 'pending',
    ratePerPost: 3500,
    preferredCommunication: 'discord',
    createdAt: '2024-02-20',
    updatedAt: '2024-03-09',
    location: 'San Francisco, CA',
    socialMediaAccounts: [
      {
        id: '3',
        kolId: '2',
        platform: 'youtube',
        username: 'MikeChenTech',
        platformUserId: 'yt_789',
        isVerified: true,
        followersCount: 1200000,
        followingCount: 300,
        postsCount: 450,
        engagementRate: 5.5,
        lastSynced: '2024-03-09',
      },
      {
        id: '4',
        kolId: '2',
        platform: 'tiktok',
        username: 'mikechentech',
        platformUserId: 'tt_101',
        isVerified: false,
        followersCount: 500000,
        followingCount: 800,
        postsCount: 890,
        engagementRate: 8.2,
        lastSynced: '2024-03-09',
      },
    ],
  },
]

interface KOLTableProps {
  onKOLSelect?: (kol: KOL) => void
  onBulkAction?: (action: string, selectedIds: string[]) => void
}

export function KOLTable({ onKOLSelect, onBulkAction }: KOLTableProps) {
  const [data, setData] = useState<KOL[]>(mockKOLs)
  const [globalFilter, setGlobalFilter] = useState('')
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({})

  // Platform color mapping
  const getPlatformColor = (platform: string) => {
    const colors = {
      instagram: 'bg-pink-100 text-pink-800',
      youtube: 'bg-red-100 text-red-800',
      tiktok: 'bg-gray-100 text-gray-800',
      twitter: 'bg-blue-100 text-blue-800',
      facebook: 'bg-indigo-100 text-indigo-800',
    }
    return colors[platform as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  // Status color mapping
  const getStatusColor = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      expired: 'bg-red-100 text-red-800',
      terminated: 'bg-gray-100 text-gray-800',
    }
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  // Column definitions
  const columns = useMemo<ColumnDef<KOL>[]>(
    () => [
      {
        id: 'select',
        header: ({ table }) => {
          const checkboxRef = useRef<HTMLInputElement>(null)
          const isAllSelected = table.getIsAllRowsSelected()
          const isSomeSelected = table.getIsSomeRowsSelected()

          useEffect(() => {
            if (checkboxRef.current) {
              checkboxRef.current.indeterminate = isSomeSelected && !isAllSelected
            }
          }, [isSomeSelected, isAllSelected])

          return (
            <Checkbox
              ref={checkboxRef}
              checked={isAllSelected}
              onCheckedChange={table.getToggleAllRowsSelectedHandler()}
            />
          )
        },
        cell: ({ row }) => (
          <Checkbox
            checked={row.getIsSelected()}
            onCheckedChange={row.getToggleSelectedHandler()}
          />
        ),
        enableSorting: false,
        enableHiding: false,
      },
      {
        accessorKey: 'name',
        header: ({ column }) => (
          <button
            className="flex items-center gap-2 hover:bg-gray-100 p-2 rounded-md -m-2"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            KOL Name
            {column.getIsSorted() === 'asc' && <ChevronUpIcon className="w-4 h-4" />}
            {column.getIsSorted() === 'desc' && <ChevronDownIcon className="w-4 h-4" />}
          </button>
        ),
        cell: ({ row }) => (
          <div className="flex items-center gap-3">
            <img
              src={row.original.avatar}
              alt={row.original.name}
              className="w-10 h-10 rounded-full object-cover"
            />
            <div>
              <p className="font-medium text-gray-900">{row.original.name}</p>
              <p className="text-sm text-gray-500">@{row.original.username}</p>
            </div>
          </div>
        ),
      },
      {
        accessorKey: 'platforms',
        header: 'Platforms',
        cell: ({ row }) => (
          <div className="flex flex-wrap gap-1">
            {row.original.socialMediaAccounts.map((account) => (
              <span
                key={account.id}
                className={cn(
                  'px-2 py-1 rounded-full text-xs font-medium capitalize',
                  getPlatformColor(account.platform)
                )}
              >
                {account.platform}
              </span>
            ))}
          </div>
        ),
        enableSorting: false,
        filterFn: (row, id, value) => {
          const platforms = row.original.socialMediaAccounts.map(acc => acc.platform)
          return value.length === 0 || value.some((v: string) => platforms.includes(v))
        },
      },
      {
        accessorKey: 'totalFollowers',
        header: ({ column }) => (
          <button
            className="flex items-center gap-2 hover:bg-gray-100 p-2 rounded-md -m-2"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Followers
            {column.getIsSorted() === 'asc' && <ChevronUpIcon className="w-4 h-4" />}
            {column.getIsSorted() === 'desc' && <ChevronDownIcon className="w-4 h-4" />}
          </button>
        ),
        cell: ({ row }) => {
          const total = row.original.socialMediaAccounts.reduce(
            (sum, acc) => sum + acc.followersCount,
            0
          )
          return (
            <span className="font-mono font-medium text-right block">
              {formatNumber(total)}
            </span>
          )
        },
        accessorFn: (row) => row.socialMediaAccounts.reduce((sum, acc) => sum + acc.followersCount, 0),
      },
      {
        accessorKey: 'avgEngagement',
        header: ({ column }) => (
          <button
            className="flex items-center gap-2 hover:bg-gray-100 p-2 rounded-md -m-2"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Engagement
            {column.getIsSorted() === 'asc' && <ChevronUpIcon className="w-4 h-4" />}
            {column.getIsSorted() === 'desc' && <ChevronDownIcon className="w-4 h-4" />}
          </button>
        ),
        cell: ({ row }) => {
          const avgEngagement = row.original.socialMediaAccounts.reduce(
            (sum, acc) => sum + acc.engagementRate,
            0
          ) / row.original.socialMediaAccounts.length

          return (
            <div className="flex items-center gap-2">
              <div className="w-20 bg-gray-200 rounded-full h-2">
                <motion.div
                  className="bg-green-500 h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(avgEngagement * 10, 100)}%` }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                />
              </div>
              <span className="text-sm font-medium">{avgEngagement.toFixed(1)}%</span>
            </div>
          )
        },
        accessorFn: (row) => row.socialMediaAccounts.reduce((sum, acc) => sum + acc.engagementRate, 0) / row.socialMediaAccounts.length,
      },
      {
        accessorKey: 'contractStatus',
        header: 'Status',
        cell: ({ getValue }) => {
          const status = getValue() as string
          return (
            <Badge variant={status === 'active' ? 'default' : status === 'pending' ? 'secondary' : 'outline'}>
              {status}
            </Badge>
          )
        },
      },
      {
        accessorKey: 'ratePerPost',
        header: ({ column }) => (
          <button
            className="flex items-center gap-2 hover:bg-gray-100 p-2 rounded-md -m-2"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Rate/Post
            {column.getIsSorted() === 'asc' && <ChevronUpIcon className="w-4 h-4" />}
            {column.getIsSorted() === 'desc' && <ChevronDownIcon className="w-4 h-4" />}
          </button>
        ),
        cell: ({ getValue }) => (
          <span className="font-mono font-medium">
            ${(getValue() as number).toLocaleString()}
          </span>
        ),
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onKOLSelect?.(row.original)}
              className="h-8 w-8 p-0"
            >
              <EyeIcon className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
            >
              <ChatBubbleLeftIcon className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
            >
              <PlusIcon className="w-4 h-4" />
            </Button>
          </div>
        ),
        enableSorting: false,
        enableHiding: false,
      },
    ],
    [onKOLSelect]
  )

  // Table instance
  const table = useReactTable({
    data,
    columns,
    state: {
      globalFilter,
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
    onGlobalFilterChange: setGlobalFilter,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  })

  // Debounced search
  const debouncedSetGlobalFilter = debounce(setGlobalFilter, 300)

  const selectedCount = Object.keys(rowSelection).length

  return (
    <Card>
      <CardHeader>
        <CardTitle>KOL Management</CardTitle>
        <CardDescription>Manage your influencer network with advanced search and filtering capabilities</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Header Controls */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-col gap-4 sm:flex-row sm:flex-1">
          {/* Search */}
          <div className="relative w-full sm:max-w-sm">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search KOLs..."
              onChange={(e) => debouncedSetGlobalFilter(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Platform Filter */}
          <select
            className="w-full sm:w-auto px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onChange={(e) => {
              const value = e.target.value
              table.getColumn('platforms')?.setFilterValue(value ? [value] : [])
            }}
          >
            <option value="">All Platforms</option>
            <option value="instagram">Instagram</option>
            <option value="youtube">YouTube</option>
            <option value="tiktok">TikTok</option>
            <option value="twitter">Twitter</option>
            <option value="facebook">Facebook</option>
          </select>
        </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:gap-2 w-full sm:w-auto">
            <Button variant="outline" size="sm" className="w-full sm:w-auto">
              <AdjustmentsHorizontalIcon className="w-4 h-4 mr-2" />
              Filters
            </Button>
            <Button variant="outline" size="sm" className="w-full sm:w-auto">
              <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Bulk Actions */}
        <AnimatePresence>
          {selectedCount > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-blue-50 border border-blue-200 rounded-lg p-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckIcon className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">
                  {selectedCount} KOL{selectedCount > 1 ? 's' : ''} selected
                </span>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onBulkAction?.('message', Object.keys(rowSelection))}
                >
                  Send Message
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onBulkAction?.('campaign', Object.keys(rowSelection))}
                >
                  Add to Campaign
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onBulkAction?.('export', Object.keys(rowSelection))}
                >
                  Export Selected
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <div className="rounded-md border overflow-x-auto">
        <Table className="min-w-[800px]">
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            <AnimatePresence>
              {table.getRowModel().rows.map((row, index) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                  className={cn(
                    "transition-colors hover:bg-muted/50",
                    row.getIsSelected() && "bg-muted"
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
          </AnimatePresence>
          </TableBody>
        </Table>

        {/* Pagination */}
        <div className="flex flex-col gap-4 px-4 py-4 border-t border-gray-200 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-center gap-2">
            <span className="text-xs sm:text-sm text-muted-foreground">
              Showing{' '}
              <span className="font-medium text-foreground">
                {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1}
              </span>{' '}
              to{' '}
              <span className="font-medium text-foreground">
                {Math.min(
                  (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                  table.getFilteredRowModel().rows.length
                )}
              </span>{' '}
              of{' '}
              <span className="font-medium text-foreground">{table.getFilteredRowModel().rows.length}</span>{' '}
              results
            </span>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="w-full sm:w-auto"
            >
              <ChevronLeftIcon className="w-4 h-4" />
              <span className="hidden sm:inline">Previous</span>
            </Button>

            <div className="flex items-center gap-1 justify-center sm:justify-start">
              {Array.from({ length: table.getPageCount() }, (_, i) => (
                <Button
                  key={i}
                  variant={table.getState().pagination.pageIndex === i ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => table.setPageIndex(i)}
                  className="w-8 h-8 p-0"
                >
                  {i + 1}
                </Button>
              )).slice(
                Math.max(0, table.getState().pagination.pageIndex - 2),
                Math.min(table.getPageCount(), table.getState().pagination.pageIndex + 3)
              )}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="w-full sm:w-auto"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRightIcon className="w-4 h-4" />
            </Button>

            <Select
              value={table.getState().pagination.pageSize.toString()}
              onValueChange={(value) => table.setPageSize(Number(value))}
            >
              <SelectTrigger className="w-full sm:w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[10, 25, 50, 100].map((pageSize) => (
                  <SelectItem key={pageSize} value={pageSize.toString()}>
                    {pageSize} per page
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
      </CardContent>
    </Card>
  )
}