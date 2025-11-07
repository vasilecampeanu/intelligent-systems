from __future__ import annotations
import argparse, os, json
import matplotlib.pyplot as plt
import numpy as np

from .model import ReplicatorWorld

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--width', type=int, default=40)
    ap.add_argument('--height', type=int, default=40)
    ap.add_argument('--steps', type=int, default=600)
    ap.add_argument('--founders', type=int, default=10)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--outdir', type=str, default='output')
    ap.add_argument('--success', type=str, default='final_alive', choices=['final_alive','total_births'])
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    model = ReplicatorWorld(width=args.width, height=args.height, seed=args.seed,
                            founders=args.founders, steps=args.steps)
    df = model.run()

    # compute success metric
    if args.success == 'final_alive':
        final_counts = {lin: series[-1] for lin, series in model.history_lineage_counts.items() if len(series)>0}
        top_lin = max(final_counts, key=final_counts.get) if final_counts else None
    else:
        top_lin = max(model.lineage_births, key=model.lineage_births.get) if model.lineage_births else None

    # Save CSV summary & meta
    df.to_csv(os.path.join(args.outdir, 'summary.csv'), index=False)
    
    # Use founder genes for each lineage
    lineage_genes = {
        int(k): {
            "replication_rate": round(v["replication_rate"], 4),
            "death_rate": round(v["death_rate"], 4),
            "mutation_rate": round(v["mutation_rate"], 4),
            "metabolism": round(v["metabolism"], 4),
        } 
        for k, v in model.lineage_founder_genes.items()
    }
    
    with open(os.path.join(args.outdir, 'meta.json'), 'w') as f:
        json.dump({
            "top_lineage": int(top_lin) if top_lin is not None else None,
            "success_metric": args.success,
            "final_alive": {int(k): int(v[-1]) for k,v in model.history_lineage_counts.items() if len(v)>0},
            "total_births": {int(k): int(v) for k,v in model.lineage_births.items()},
            "lineage_genes": {int(k): v for k, v in lineage_genes.items()},
        }, f, indent=2)
    
    # Create a detailed human-readable report
    report_file = os.path.join(args.outdir, 'simulation_report.txt')
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("REPLICATOR EVOLUTION SIMULATION REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Simulation Parameters:\n")
        f.write(f"  • Grid Size: {args.width} x {args.height}\n")
        f.write(f"  • Time Steps: {args.steps}\n")
        f.write(f"  • Founder Lineages: {args.founders}\n")
        f.write(f"  • Random Seed: {args.seed}\n")
        f.write(f"  • Success Metric: {args.success}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("COMPETITION RESULTS\n")
        f.write("-" * 80 + "\n\n")
        
        # Sort lineages by final population
        lineage_results = []
        for lin in model.lineage_founder_genes.keys():
            final_pop = final_counts.get(lin, 0)
            total_births = model.lineage_births.get(lin, 0)
            survival_rate = (final_pop / total_births * 100) if total_births > 0 else 0
            lineage_results.append((lin, final_pop, total_births, survival_rate))
        
        lineage_results.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (lin, final_pop, total_births, survival_rate) in enumerate(lineage_results, 1):
            genes = model.lineage_founder_genes[lin]
            f.write(f"Rank #{rank}: Lineage {lin}\n")
            f.write(f"  Final Population: {final_pop:,}\n")
            f.write(f"  Total Births: {total_births:,}\n")
            f.write(f"  Survival Rate: {survival_rate:.2f}%\n")
            f.write(f"  Founding Genome:\n")
            f.write(f"    - Replication Rate: {genes['replication_rate']:.4f}\n")
            f.write(f"    - Death Rate: {genes['death_rate']:.4f}\n")
            f.write(f"    - Mutation Rate: {genes['mutation_rate']:.4f}\n")
            f.write(f"    - Metabolism: {genes['metabolism']:.4f}\n")
            
            if rank == 1:
                f.write(f"  🏆 WINNER!\n")
            f.write("\n")
        
        f.write("-" * 80 + "\n")
        f.write("EVOLUTIONARY INSIGHTS\n")
        f.write("-" * 80 + "\n\n")
        
        # Calculate averages
        winner_genes = model.lineage_founder_genes[lineage_results[0][0]]
        avg_replication = np.mean([g['replication_rate'] for g in model.lineage_founder_genes.values()])
        avg_death = np.mean([g['death_rate'] for g in model.lineage_founder_genes.values()])
        avg_mutation = np.mean([g['mutation_rate'] for g in model.lineage_founder_genes.values()])
        avg_metabolism = np.mean([g['metabolism'] for g in model.lineage_founder_genes.values()])
        
        f.write(f"Winner's Competitive Advantages (Lineage {lineage_results[0][0]}):\n")
        f.write(f"  • Replication Rate: {winner_genes['replication_rate']:.4f} (avg: {avg_replication:.4f})\n")
        f.write(f"  • Death Rate: {winner_genes['death_rate']:.4f} (avg: {avg_death:.4f})\n")
        f.write(f"  • Mutation Rate: {winner_genes['mutation_rate']:.4f} (avg: {avg_mutation:.4f})\n")
        f.write(f"  • Metabolism: {winner_genes['metabolism']:.4f} (avg: {avg_metabolism:.4f})\n\n")
        
        # Key factors
        f.write("Key Success Factors:\n")
        if winner_genes['death_rate'] < avg_death:
            f.write("  ✓ Below-average death rate (better survival)\n")
        if winner_genes['metabolism'] < avg_metabolism:
            f.write("  ✓ Below-average metabolism (energy efficiency)\n")
        if winner_genes['replication_rate'] > avg_replication:
            f.write("  ✓ Above-average replication rate (faster growth)\n")
        
        f.write("\n" + "=" * 80 + "\n")
    
    print(f"✓ Detailed report saved to: {report_file}")

    # ==============================================================
    # GRAPH 1: Main competition plot over time
    # ==============================================================
    plt.figure(figsize=(14, 7))
    for lin in sorted(model.history_lineage_counts.keys()):
        y = model.history_lineage_counts[lin]
        xs = np.arange(1, len(y) + 1)
        label = f"Lineage {lin}"
        plt.plot(xs, y, label=label, linewidth=2.5, alpha=0.85)
    
    plt.xlabel("Time Step", fontsize=13)
    plt.ylabel("Population", fontsize=13)
    plt.title(f"Lineage Competition Over Time\n(seed={args.seed}, steps={args.steps}, founders={args.founders})", 
              fontsize=15, fontweight='bold')
    plt.legend(loc='best', fontsize=11, ncol=2, framealpha=0.9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    outfile_time = os.path.join(args.outdir, '1_competition_timeline.png')
    plt.savefig(outfile_time, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Timeline plot saved to: {outfile_time}")
    
    # ==============================================================
    # GRAPH 2: Replication vs Death Rate scatter
    # ==============================================================
    plt.figure(figsize=(10, 8))
    lineages = sorted(model.lineage_founder_genes.keys())
    colors = plt.cm.tab10(np.linspace(0, 1, len(lineages)))
    
    for i, lin in enumerate(lineages):
        genes = model.lineage_founder_genes[lin]
        final_pop = final_counts.get(lin, 0)
        size = 200 + (final_pop / max(final_counts.values()) * 800) if final_counts and max(final_counts.values()) > 0 else 200
        plt.scatter(genes['replication_rate'], genes['death_rate'], 
                   s=size, c=[colors[i]], alpha=0.7, edgecolors='black', linewidth=2,
                   label=f"L{lin} (pop={final_pop:,})", zorder=3)
    
    plt.xlabel("Replication Rate", fontsize=13)
    plt.ylabel("Death Rate", fontsize=13)
    plt.title("Replication vs Death Rate\n(bubble size = final population)", fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, loc='best', framealpha=0.9)
    plt.grid(True, alpha=0.3, zorder=1)
    plt.tight_layout()
    outfile_rep_death = os.path.join(args.outdir, '2_replication_vs_death.png')
    plt.savefig(outfile_rep_death, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Replication vs Death plot saved to: {outfile_rep_death}")
    
    # ==============================================================
    # GRAPH 3: Metabolism vs Mutation Rate scatter
    # ==============================================================
    plt.figure(figsize=(10, 8))
    for i, lin in enumerate(lineages):
        genes = model.lineage_founder_genes[lin]
        final_pop = final_counts.get(lin, 0)
        size = 200 + (final_pop / max(final_counts.values()) * 800) if final_counts and max(final_counts.values()) > 0 else 200
        plt.scatter(genes['metabolism'], genes['mutation_rate'], 
                   s=size, c=[colors[i]], alpha=0.7, edgecolors='black', linewidth=2,
                   label=f"L{lin} (pop={final_pop:,})", zorder=3)
    
    plt.xlabel("Metabolism", fontsize=13)
    plt.ylabel("Mutation Rate", fontsize=13)
    plt.title("Metabolism vs Mutation Rate\n(bubble size = final population)", fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, loc='best', framealpha=0.9)
    plt.grid(True, alpha=0.3, zorder=1)
    plt.tight_layout()
    outfile_met_mut = os.path.join(args.outdir, '3_metabolism_vs_mutation.png')
    plt.savefig(outfile_met_mut, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Metabolism vs Mutation plot saved to: {outfile_met_mut}")
    
    # ==============================================================
    # GRAPH 4: Gene heatmap
    # ==============================================================
    fig, ax = plt.subplots(figsize=(12, 6))
    gene_names = ['replication_rate', 'death_rate', 'mutation_rate', 'metabolism']
    gene_matrix = []
    for lin in lineages:
        genes = model.lineage_founder_genes[lin]
        gene_matrix.append([genes[gn] for gn in gene_names])
    
    gene_matrix = np.array(gene_matrix)
    im = ax.imshow(gene_matrix.T, aspect='auto', cmap='YlOrRd', interpolation='nearest')
    ax.set_xticks(range(len(lineages)))
    ax.set_xticklabels([f"L{lin}" for lin in lineages], fontsize=11)
    ax.set_yticks(range(len(gene_names)))
    ax.set_yticklabels(['Replication Rate', 'Death Rate', 'Mutation Rate', 'Metabolism'], fontsize=11)
    ax.set_xlabel("Lineage", fontsize=13)
    ax.set_title("Founder Gene Values Heatmap", fontsize=14, fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Value', rotation=270, labelpad=20, fontsize=12)
    
    # Add text annotations
    for i in range(len(lineages)):
        for j in range(len(gene_names)):
            text = ax.text(i, j, f'{gene_matrix[i, j]:.3f}',
                          ha="center", va="center", color="black", fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    outfile_heatmap = os.path.join(args.outdir, '4_gene_heatmap.png')
    plt.savefig(outfile_heatmap, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Gene heatmap saved to: {outfile_heatmap}")
    
    # ==============================================================
    # GRAPH 5: Statistics summary table
    # ==============================================================
    fig, ax = plt.subplots(figsize=(10, max(8, len(lineages) * 0.6)))
    ax.axis('off')
    
    # Create summary statistics
    table_data = [['Rank', 'Lineage', 'Final Pop', 'Total Births', 'Survival %']]
    
    # Sort lineages by final population
    lineage_results = []
    for lin in lineages:
        final_pop = final_counts.get(lin, 0)
        total_births = model.lineage_births.get(lin, 0)
        survival = (final_pop / total_births * 100) if total_births > 0 else 0
        lineage_results.append((lin, final_pop, total_births, survival))
    
    lineage_results.sort(key=lambda x: x[1], reverse=True)
    
    for rank, (lin, final_pop, total_births, survival) in enumerate(lineage_results, 1):
        table_data.append([f'#{rank}', f'L{lin}', f'{final_pop:,}', f'{total_births:,}', f'{survival:.1f}%'])
    
    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.12, 0.15, 0.25, 0.25, 0.23])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    # Style header
    for i in range(5):
        table[(0, i)].set_facecolor('#2E7D32')
        table[(0, i)].set_text_props(weight='bold', color='white', fontsize=12)
    
    # Highlight top 3
    colors = ['#FFD700', '#C0C0C0', '#CD7F32']  # Gold, Silver, Bronze
    for i in range(min(3, len(lineage_results))):
        for j in range(5):
            table[(i + 1, j)].set_facecolor(colors[i])
            table[(i + 1, j)].set_text_props(weight='bold', fontsize=11)
    
    ax.set_title(f"Competition Statistics\n(seed={args.seed}, steps={args.steps})", 
                fontsize=14, fontweight='bold', pad=30)
    
    plt.tight_layout()
    outfile_table = os.path.join(args.outdir, '5_statistics_table.png')
    plt.savefig(outfile_table, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Statistics table saved to: {outfile_table}")
    
    # ==============================================================
    # GRAPH 6: Lineage Genes Table
    # ==============================================================
    fig, ax = plt.subplots(figsize=(14, max(8, len(lineages) * 0.7)))
    ax.axis('off')
    
    # Create gene table with all lineages
    table_data = [['Lineage', 'Replication\nRate', 'Death\nRate', 'Mutation\nRate', 'Metabolism', 'Final\nPopulation']]
    
    for lin in lineages:
        genes = model.lineage_founder_genes[lin]
        final_pop = final_counts.get(lin, 0)
        table_data.append([
            f'L{lin}',
            f'{genes["replication_rate"]:.4f}',
            f'{genes["death_rate"]:.4f}',
            f'{genes["mutation_rate"]:.4f}',
            f'{genes["metabolism"]:.4f}',
            f'{final_pop:,}'
        ])
    
    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.12, 0.18, 0.18, 0.18, 0.18, 0.16])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 3)
    
    # Style header
    for i in range(6):
        table[(0, i)].set_facecolor('#1976D2')
        table[(0, i)].set_text_props(weight='bold', color='white', fontsize=11)
    
    # Highlight rows based on final population
    max_pop = max(final_counts.values()) if final_counts else 0
    for i, lin in enumerate(lineages, 1):
        final_pop = final_counts.get(lin, 0)
        if final_pop == max_pop and max_pop > 0:
            # Winner - gold
            for j in range(6):
                table[(i, j)].set_facecolor('#FFD700')
                table[(i, j)].set_text_props(weight='bold', fontsize=11)
        elif final_pop > 0:
            # Survivors - light green
            for j in range(6):
                table[(i, j)].set_facecolor('#C8E6C9')
                table[(i, j)].set_text_props(fontsize=10)
        else:
            # Extinct - light gray
            for j in range(6):
                table[(i, j)].set_facecolor('#F5F5F5')
                table[(i, j)].set_text_props(fontsize=10, color='#666666')
    
    ax.set_title(f"Lineage Founder Genes and Final Populations\n(seed={args.seed}, steps={args.steps})", 
                fontsize=15, fontweight='bold', pad=30)
    
    # Add legend
    legend_text = ""
    fig.text(0.5, 0.05, legend_text, ha='center', fontsize=11, style='italic')
    
    plt.tight_layout()
    outfile_genes = os.path.join(args.outdir, '6_lineage_genes_table.png')
    plt.savefig(outfile_genes, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✓ Lineage genes table saved to: {outfile_genes}")
    
    print(f"\n{'='*60}")
    print(f"All visualizations complete! Output directory: {args.outdir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
