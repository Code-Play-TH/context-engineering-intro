import { create } from 'zustand'
import { KOL, TableState } from '@/types'

interface KOLState {
  kols: KOL[]
  selectedKols: string[]
  tableState: TableState
  totalCount: number
  isLoading: boolean
  error: string | null

  // Actions
  fetchKOLs: () => Promise<void>
  setKOLs: (kols: KOL[]) => void
  updateKOL: (id: string, updates: Partial<KOL>) => void
  deleteKOL: (id: string) => void
  setSelectedKols: (ids: string[]) => void
  setTableState: (state: Partial<TableState>) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useKOLStore = create<KOLState>((set, get) => ({
  kols: [],
  selectedKols: [],
  tableState: {
    globalFilter: '',
    sorting: [],
    columnFilters: [],
    rowSelection: {},
    pagination: {
      pageIndex: 0,
      pageSize: 25,
    },
  },
  totalCount: 0,
  isLoading: false,
  error: null,

  fetchKOLs: async () => {
    const { tableState } = get()
    set({ isLoading: true, error: null })

    try {
      const params = new URLSearchParams({
        page: (tableState.pagination.pageIndex + 1).toString(),
        limit: tableState.pagination.pageSize.toString(),
        search: tableState.globalFilter,
        sort: JSON.stringify(tableState.sorting),
        filters: JSON.stringify(tableState.columnFilters),
      })

      const response = await fetch(`/api/kols?${params}`)

      if (!response.ok) {
        throw new Error('Failed to fetch KOLs')
      }

      const data = await response.json()

      set({
        kols: data.kols,
        totalCount: data.total,
        isLoading: false,
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Unknown error',
        isLoading: false,
      })
    }
  },

  setKOLs: (kols: KOL[]) => {
    set({ kols })
  },

  updateKOL: (id: string, updates: Partial<KOL>) => {
    set((state) => ({
      kols: state.kols.map((kol) =>
        kol.id === id ? { ...kol, ...updates } : kol
      ),
    }))
  },

  deleteKOL: (id: string) => {
    set((state) => ({
      kols: state.kols.filter((kol) => kol.id !== id),
      selectedKols: state.selectedKols.filter((selectedId) => selectedId !== id),
    }))
  },

  setSelectedKols: (ids: string[]) => {
    set({ selectedKols: ids })
  },

  setTableState: (newState: Partial<TableState>) => {
    set((state) => ({
      tableState: { ...state.tableState, ...newState },
    }))
    // Automatically fetch new data when table state changes
    setTimeout(() => get().fetchKOLs(), 0)
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading })
  },

  setError: (error: string | null) => {
    set({ error })
  },
}))