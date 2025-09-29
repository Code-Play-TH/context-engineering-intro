'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import * as d3 from 'd3'

interface DataPoint {
  date: string
  value: number
  label?: string
}

interface LineChartProps {
  data: DataPoint[]
  width?: number
  height?: number
  title?: string
  color?: string
  animate?: boolean
}

export function LineChart({
  data,
  width = 800,
  height = 400,
  title,
  color = '#3B82F6',
  animate = true
}: LineChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current || !data.length) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const margin = { top: 20, right: 30, bottom: 40, left: 50 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Parse dates
    const parseDate = d3.timeParse('%Y-%m-%d')
    const processedData = data.map(d => ({
      ...d,
      date: parseDate(d.date) || new Date(),
    }))

    // Scales
    const xScale = d3
      .scaleTime()
      .domain(d3.extent(processedData, d => d.date) as [Date, Date])
      .range([0, innerWidth])

    const yScale = d3
      .scaleLinear()
      .domain(d3.extent(processedData, d => d.value) as [number, number])
      .nice()
      .range([innerHeight, 0])

    // Line generator
    const line = d3
      .line<any>()
      .x(d => xScale(d.date))
      .y(d => yScale(d.value))
      .curve(d3.curveCardinal)

    // Add axes
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat('%m/%d') as any))

    g.append('g')
      .call(d3.axisLeft(yScale))

    // Add grid lines
    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(
        d3.axisBottom(xScale)
          .tickSize(-innerHeight)
          .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    g.append('g')
      .attr('class', 'grid')
      .call(
        d3.axisLeft(yScale)
          .tickSize(-innerWidth)
          .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    // Add area under line
    const area = d3
      .area<any>()
      .x(d => xScale(d.date))
      .y0(innerHeight)
      .y1(d => yScale(d.value))
      .curve(d3.curveCardinal)

    const areaPath = g
      .append('path')
      .datum(processedData)
      .attr('fill', color)
      .attr('opacity', 0.1)
      .attr('d', area)

    // Add line
    const linePath = g
      .append('path')
      .datum(processedData)
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 3)
      .attr('d', line)

    // Add dots
    const dots = g
      .selectAll('.dot')
      .data(processedData)
      .enter()
      .append('circle')
      .attr('class', 'dot')
      .attr('cx', d => xScale(d.date))
      .attr('cy', d => yScale(d.value))
      .attr('r', 4)
      .attr('fill', color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)

    // Animate if enabled
    if (animate) {
      const totalLength = linePath.node()?.getTotalLength() || 0

      linePath
        .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
        .attr('stroke-dashoffset', totalLength)
        .transition()
        .duration(2000)
        .ease(d3.easeLinear)
        .attr('stroke-dashoffset', 0)

      dots
        .attr('r', 0)
        .transition()
        .duration(1000)
        .delay((d, i) => i * 100)
        .attr('r', 4)

      areaPath
        .attr('opacity', 0)
        .transition()
        .duration(1500)
        .delay(500)
        .attr('opacity', 0.1)
    }

    // Add tooltip
    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'tooltip')
      .style('position', 'absolute')
      .style('background', 'rgba(0, 0, 0, 0.8)')
      .style('color', 'white')
      .style('padding', '8px')
      .style('border-radius', '4px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('opacity', 0)

    dots
      .on('mouseover', function(event, d) {
        tooltip
          .style('opacity', 1)
          .html(`
            <div>Date: ${d3.timeFormat('%Y-%m-%d')(d.date)}</div>
            <div>Value: ${d.value.toLocaleString()}</div>
            ${d.label ? `<div>${d.label}</div>` : ''}
          `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px')

        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 6)
      })
      .on('mouseout', function() {
        tooltip.style('opacity', 0)
        d3.select(this)
          .transition()
          .duration(200)
          .attr('r', 4)
      })

    return () => {
      tooltip.remove()
    }
  }, [data, width, height, color, animate])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass rounded-lg p-6"
    >
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="w-full h-auto"
        viewBox={`0 0 ${width} ${height}`}
      />
    </motion.div>
  )
}