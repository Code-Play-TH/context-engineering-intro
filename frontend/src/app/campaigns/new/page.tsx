'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useCreateCampaign } from '@/hooks/useCampaigns';
import { Card } from '@/components/ui/card';

export default function NewCampaignPage() {
    const router = useRouter();
    const createMutation = useCreateCampaign();

    const [formData, setFormData] = useState({
        name: '',
        start_date: '',
        end_date: '',
        total_budget: '',
        currency: 'USD',
        objectives: '',
        target_audience: '',
    });

    const [kpis, setKpis] = useState<Array<{ kpi_type: string; target_value: string; unit: string }>>([]);
    const [deliverables, setDeliverables] = useState<Array<{ deliverable_type: string; quantity: string; deadline: string }>>([]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            const campaign = await createMutation.mutateAsync({
                name: formData.name,
                start_date: formData.start_date || undefined,
                end_date: formData.end_date || undefined,
                total_budget: formData.total_budget ? parseFloat(formData.total_budget) : undefined,
                currency: formData.currency,
                objectives: formData.objectives || undefined,
                target_audience: formData.target_audience ? JSON.parse(formData.target_audience) : undefined,
                kpis: kpis.map(k => ({
                    kpi_type: k.kpi_type,
                    target_value: parseFloat(k.target_value),
                    unit: k.unit,
                })),
                deliverables: deliverables.map(d => ({
                    deliverable_type: d.deliverable_type,
                    quantity: parseInt(d.quantity),
                    deadline: d.deadline || undefined,
                })),
            });

            alert('Campaign created successfully!');
            router.push(`/campaigns/${campaign.id}`);
        } catch (error: any) {
            alert(error.message || 'Failed to create campaign');
        }
    };

    const addKPI = () => {
        setKpis([...kpis, { kpi_type: '', target_value: '', unit: '' }]);
    };

    const removeKPI = (index: number) => {
        setKpis(kpis.filter((_, i) => i !== index));
    };

    const updateKPI = (index: number, field: string, value: string) => {
        const updated = [...kpis];
        updated[index] = { ...updated[index], [field]: value };
        setKpis(updated);
    };

    const addDeliverable = () => {
        setDeliverables([...deliverables, { deliverable_type: '', quantity: '', deadline: '' }]);
    };

    const removeDeliverable = (index: number) => {
        setDeliverables(deliverables.filter((_, i) => i !== index));
    };

    const updateDeliverable = (index: number, field: string, value: string) => {
        const updated = [...deliverables];
        updated[index] = { ...updated[index], [field]: value };
        setDeliverables(updated);
    };

    return (
        <div className="container mx-auto px-4 py-8 max-w-4xl">
            <div className="mb-6">
                <h1 className="text-3xl font-bold">Create New Campaign</h1>
                <p className="text-gray-600 mt-2">Fill in the details to create a new campaign</p>
            </div>

            <form onSubmit={handleSubmit}>
                <Card className="p-6 mb-6">
                    <h2 className="text-xl font-semibold mb-4">Basic Information</h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">
                                Campaign Name <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                required
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                placeholder="Enter campaign name"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Start Date</label>
                                <input
                                    type="date"
                                    value={formData.start_date}
                                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">End Date</label>
                                <input
                                    type="date"
                                    value={formData.end_date}
                                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Budget</label>
                                <input
                                    type="number"
                                    step="0.01"
                                    value={formData.total_budget}
                                    onChange={(e) => setFormData({ ...formData, total_budget: e.target.value })}
                                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                    placeholder="0.00"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">Currency</label>
                                <select
                                    value={formData.currency}
                                    onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                >
                                    <option value="USD">USD</option>
                                    <option value="EUR">EUR</option>
                                    <option value="THB">THB</option>
                                    <option value="GBP">GBP</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Objectives</label>
                            <textarea
                                value={formData.objectives}
                                onChange={(e) => setFormData({ ...formData, objectives: e.target.value })}
                                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                rows={4}
                                placeholder="Describe campaign objectives..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">
                                Target Audience (JSON)
                            </label>
                            <textarea
                                value={formData.target_audience}
                                onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                                rows={3}
                                placeholder='{"age": "18-35", "gender": "all", "interests": ["fashion", "lifestyle"]}'
                            />
                        </div>
                    </div>
                </Card>

                <Card className="p-6 mb-6">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-semibold">KPIs</h2>
                        <button
                            type="button"
                            onClick={addKPI}
                            className="px-3 py-1 text-sm bg-primary text-white rounded hover:bg-primary/90"
                        >
                            Add KPI
                        </button>
                    </div>

                    {kpis.length === 0 ? (
                        <p className="text-gray-500 text-sm">No KPIs added yet</p>
                    ) : (
                        <div className="space-y-3">
                            {kpis.map((kpi, index) => (
                                <div key={index} className="flex gap-3 items-start">
                                    <input
                                        type="text"
                                        value={kpi.kpi_type}
                                        onChange={(e) => updateKPI(index, 'kpi_type', e.target.value)}
                                        className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="KPI Type (e.g., Reach, Engagement)"
                                    />
                                    <input
                                        type="number"
                                        value={kpi.target_value}
                                        onChange={(e) => updateKPI(index, 'target_value', e.target.value)}
                                        className="w-32 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="Target"
                                    />
                                    <input
                                        type="text"
                                        value={kpi.unit}
                                        onChange={(e) => updateKPI(index, 'unit', e.target.value)}
                                        className="w-32 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="Unit"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => removeKPI(index)}
                                        className="px-3 py-2 text-red-600 border border-red-300 rounded hover:bg-red-50"
                                    >
                                        Remove
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </Card>

                <Card className="p-6 mb-6">
                    <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-semibold">Deliverables</h2>
                        <button
                            type="button"
                            onClick={addDeliverable}
                            className="px-3 py-1 text-sm bg-primary text-white rounded hover:bg-primary/90"
                        >
                            Add Deliverable
                        </button>
                    </div>

                    {deliverables.length === 0 ? (
                        <p className="text-gray-500 text-sm">No deliverables added yet</p>
                    ) : (
                        <div className="space-y-3">
                            {deliverables.map((deliverable, index) => (
                                <div key={index} className="flex gap-3 items-start">
                                    <input
                                        type="text"
                                        value={deliverable.deliverable_type}
                                        onChange={(e) => updateDeliverable(index, 'deliverable_type', e.target.value)}
                                        className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="Type (e.g., Instagram Post, TikTok Video)"
                                    />
                                    <input
                                        type="number"
                                        value={deliverable.quantity}
                                        onChange={(e) => updateDeliverable(index, 'quantity', e.target.value)}
                                        className="w-24 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                        placeholder="Qty"
                                    />
                                    <input
                                        type="date"
                                        value={deliverable.deadline}
                                        onChange={(e) => updateDeliverable(index, 'deadline', e.target.value)}
                                        className="w-40 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => removeDeliverable(index)}
                                        className="px-3 py-2 text-red-600 border border-red-300 rounded hover:bg-red-50"
                                    >
                                        Remove
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </Card>

                <div className="flex gap-4">
                    <button
                        type="submit"
                        disabled={createMutation.isPending}
                        className="px-6 py-2 bg-primary text-white rounded hover:bg-primary/90 disabled:opacity-50"
                    >
                        {createMutation.isPending ? 'Creating...' : 'Create Campaign'}
                    </button>
                    <button
                        type="button"
                        onClick={() => router.back()}
                        className="px-6 py-2 border rounded hover:bg-gray-50"
                    >
                        Cancel
                    </button>
                </div>
            </form>
        </div>
    );
}
