"""Tests for ANATEL connectors."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("pandas", exc_type=ImportError)

from data_pipeline.connectors.anatel_smart_connector import AnatelSmartConnector
from data_pipeline.connectors.anatel_static_connector import ANATELStaticConnector


class TestAnatelStaticConnector:
    """Tests for ANATELStaticConnector."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        manual_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        yield Path(manual_dir), Path(output_dir)
        # Cleanup
        shutil.rmtree(manual_dir)
        shutil.rmtree(output_dir)
    
    def test_connector_initialization(self, temp_dirs):
        """Test connector initialization."""
        manual_dir, output_dir = temp_dirs
        connector = ANATELStaticConnector(manual_dir=manual_dir, output_dir=output_dir)
        
        assert connector.manual_dir == manual_dir
        assert connector.output_dir == output_dir
        assert manual_dir.exists()
        assert output_dir.exists()
    
    def test_find_csv_files_empty(self, temp_dirs):
        """Test finding CSV files in empty directory."""
        manual_dir, output_dir = temp_dirs
        connector = ANATELStaticConnector(manual_dir=manual_dir, output_dir=output_dir)
        
        csv_files = connector.discover_new_files()
        assert len(csv_files) == 0
    
    def test_process_csv_file(self, temp_dirs):
        """Test processing a single CSV file."""
        manual_dir, output_dir = temp_dirs
        
        # Create a sample ANATEL backhaul CSV (comma-separated)
        csv_path = manual_dir / "Anatel_Backhaul_Test.csv"
        csv_content = (
            "id,municipio,uf,operadora,latitude,longitude,frequencia,capacidade_mbps\n"
            "BH001,São Paulo,SP,Claro,-23.5505,-46.6333,2.4 GHz,100\n"
            "BH002,Rio de Janeiro,RJ,Vivo,-22.9068,-43.1729,5 GHz,200\n"
        )
        csv_path.write_text(csv_content, encoding="utf-8")

        connector = ANATELStaticConnector(manual_dir=manual_dir, output_dir=output_dir)
        result = connector.process_file(csv_path)

        assert result["status"] == "success"
        assert "stats" in result
        assert result["stats"]["arquivo_origem"] == csv_path.name
        assert result["stats"]["dataset_tipo"] == "backhaul"
        assert result["stats"]["registros_processados"] == 2

        # Check output parquet file was created
        output_files = list(output_dir.glob("*.parquet"))
        assert len(output_files) == 1
    
    def test_run_with_multiple_files(self, temp_dirs):
        """Test running connector with multiple CSV files."""
        manual_dir, output_dir = temp_dirs
        
        # Create multiple valid ANATEL CSV files
        csv1 = manual_dir / "Anatel_Backhaul_File1.csv"
        csv1.write_text(
            "id,municipio,uf,operadora,latitude,longitude,frequencia,capacidade_mbps\n"
            "BH001,São Paulo,SP,Claro,-23.5505,-46.6333,2.4 GHz,100\n",
            encoding="utf-8",
        )

        csv2 = manual_dir / "Anatel_Estacao_File2.csv"
        csv2.write_text(
            "id,municipio,uf,operadora,tecnologia,latitude,longitude\n"
            "EST001,Rio de Janeiro,RJ,Vivo,4G,-22.9068,-43.1729\n",
            encoding="utf-8",
        )

        connector = ANATELStaticConnector(manual_dir=manual_dir, output_dir=output_dir)
        results = connector.run()

        assert len(results) == 2
        assert all(r.get("status") == "success" for r in results)

        # Two parquet outputs + one JSON processing report
        output_parquets = list(output_dir.glob("*.parquet"))
        assert len(output_parquets) == 2

        report_files = list(output_dir.glob("relatorio_processamento_*.json"))
        assert len(report_files) == 1


class TestAnatelSmartConnector:
    """Tests for AnatelSmartConnector."""
    
    @pytest.fixture
    def temp_dirs_with_inventory(self):
        """Create temporary directories with inventory file."""
        manual_dir = tempfile.mkdtemp()
        manual_path = Path(manual_dir)
        
        # Create sample inventory
        inventory_content = """Item;Nome da Base de Dados;Descrição da Base de Dados;Periodicidade de Atualização;Link dados.gov.br;Link Painéis de Dados da Anatel
1;Cobertura Móvel;Dados de cobertura da telefonia móvel;Mensal;https://dados.gov.br/dataset/cobertura;
2;Estações Rádio;Estações de rádio com coordenadas;Mensal;https://dados.gov.br/dataset/estacoes;
3;Acessos Banda Larga;Dados de acessos de banda larga;Mensal;https://dados.gov.br/dataset/acessos;
4;Reclamações;Dados de reclamações de usuários;Mensal;https://dados.gov.br/dataset/reclamacoes;"""
        
        inventory_path = manual_path / "Inventario_de_Bases_de_Dados.csv"
        inventory_path.write_text(inventory_content, encoding='utf-8')
        
        yield manual_path, inventory_path
        # Cleanup
        shutil.rmtree(manual_dir)
    
    def test_connector_initialization_with_inventory(self, temp_dirs_with_inventory):
        """Test connector initialization with inventory."""
        manual_dir, inventory_path = temp_dirs_with_inventory
        
        connector = AnatelSmartConnector(inventory_path)
        
        assert connector.inventory is not None
        assert len(connector.inventory) == 4
        assert 'categoria' in connector.inventory.columns
        assert 'prioridade' in connector.inventory.columns
    
    def test_dataset_classification(self, temp_dirs_with_inventory):
        """Test dataset classification logic."""
        manual_dir, inventory_path = temp_dirs_with_inventory
        
        connector = AnatelSmartConnector(inventory_path)
        
        # Check classification
        categories = connector.inventory['categoria'].value_counts()
        
        # Should have at least one of each category
        assert 'infraestrutura_alta' in categories.index
        assert 'outros' in categories.index
        
        # Cobertura and Estações should be high priority
        high_priority = connector.inventory[
            connector.inventory['categoria'] == 'infraestrutura_alta'
        ]
        assert any('Cobertura' in name for name in high_priority['Nome da Base de Dados'])
        assert any('Estações' in name for name in high_priority['Nome da Base de Dados'])
    
    def test_show_priority_datasets(self, temp_dirs_with_inventory, capsys):
        """Test showing priority datasets."""
        manual_dir, inventory_path = temp_dirs_with_inventory
        
        connector = AnatelSmartConnector(inventory_path)
        connector.show_priority_datasets(limit=5)
        
        captured = capsys.readouterr()
        assert '🎯 DATASETS DE ALTA PRIORIDADE' in captured.out
        assert 'INFRAESTRUTURA_ALTA' in captured.out.upper()
    
    def test_generate_download_guide(self, temp_dirs_with_inventory):
        """Test download guide generation."""
        manual_dir, inventory_path = temp_dirs_with_inventory
        
        connector = AnatelSmartConnector(inventory_path)
        guide_path = connector.generate_download_guide()
        
        assert guide_path is not None
        assert guide_path.exists()
        
        # Check guide content
        content = guide_path.read_text(encoding='utf-8')
        assert '# Guia para Download de Datasets Prioritários da ANATEL' in content
        assert '## 🎯 Datasets Mais Importantes' in content
        assert 'Cobertura' in content or 'Estações' in content
    
    def test_process_all_manual_files_with_report(self, temp_dirs_with_inventory):
        """Test processing files and generating consolidated report."""
        manual_dir, inventory_path = temp_dirs_with_inventory
        
        # Create a test CSV file
        csv_path = manual_dir / "test_data.csv"
        csv_path.write_text("A;B\n1;2", encoding='utf-8')
        
        connector = AnatelSmartConnector(inventory_path)
        results = connector.process_all_manual_files()
        
        # Should process the inventory and test CSV
        assert len(results) >= 1
        
        # Check that report was generated
        report_files = list(connector.output_dir.glob("relatorio_consolidado_*.json"))
        assert len(report_files) >= 1
        
        # Verify report content
        with open(report_files[0], encoding='utf-8') as f:
            report = json.load(f)
        
        assert 'metadata' in report
        assert 'processamento' in report
        assert 'datasets_prioritarios_disponiveis' in report
        # The inventory should have the correct count from the test fixture
        assert report['metadata']['inventario_utilizado'] == 'Inventario_de_Bases_de_Dados.csv'
    
    def test_connector_without_inventory(self):
        """Test connector behavior without inventory file."""
        connector = AnatelSmartConnector(Path("nonexistent_inventory.csv"))
        
        assert connector.inventory is None
        
        # Should still work but warn
        connector.show_priority_datasets()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
