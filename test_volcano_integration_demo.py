#!/usr/bin/env python3
"""
Test script for Vo
Validates demo functis
"""

import os
import sys
import ti
import json
ath
from upatch

# Add project root to path


def test_demo_imports():
    """Test that allted"""
    print("🔍 Testing demo imports...")
    
    try:
        from demo_sult
        print("✅ Demo classes imported successfully")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_demo_initialization():
    """Te"
    prin")
    
    try:
        # Mock the depende calls
        with patch('demo_vo \
             patch('demo_v\
             patch('demo_volcano_logger:
            
         e mocks
        "]
            mock_handler.r)
            mock_logger.return_value =Mock()
            
            from demo_volcano_integration impoemo
            
        
            
            print("✅ Demo initialized succes
            print(f"   Sa
            print(f"   Results list: {len(demo.re
            print(f"   Performance data: {len(d
            
        ue
            
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        alse

def test_performance_metrics():
    """Test PerformanceMetrics dataclass"""
    print("🔍 Testing Perfo)
    
    try:
        from demo_volcano_integration ietrics
        
        
        metric = PerformanceMetrics(
            provider="volcano",
            response_time=1.23,
            token_count=150,
            success=True,
            content_type="text",
            analysis_quality_score=8.5
        )
        
        assert metri"
        assert metric.response_time == 1.23
        assert metric.success is True
        
        # Test failed metric
        failed_metretrics(
        e",
            response_time=
            success=False,
            error_messag
            content_type="tex"
        )
        
        assert flse
        assert failed_metric.error_messtimeout"
        
ctly")
 True
        
    except Exceptio as e:
        print(f"❌ Performan}")
    

def test_demo_resu():
    """Test DemoResult dataclass"""
    prin
    
    try:
        from demo_volcano_integrceMetrics
        
        metrics = [
         text"),
        xt")
        ]
        
        
            demoDemo",
            success=True,
        s,
            outpt"
        )
        
        st Demo"
        assert result.suc
        assert len(result.metrics) == 2
        
        print("✅ DemoResult working correctly")
        return True
        
    except Exception as e:
        print(f"❌ DemoResult test failed:
        se

def test_configuration_check():
    """Test configuration c"""
    print("🔍 Testing configuration check...")
    
    try:
        ent
        original_API_KEY')
        original_ark_key = oY')
        
        # Test w
        if 'GOOGLE_API_KEY' in os.envi:
            del os.environ['GOOGLE_API_KEY']
        if 'ARK_API_KEY' in os.environ:
        ]
        
        with patch('demo_vo
             patch('demo_volcano_integration.
             patch('demo_volcano_integration.setup_logger') as mock_logger:
            
            mock_manager.return_value.get_available_providers.r]
            
        nDemo
            
            # This should not crash even without API keys
            demo = VolcanoIntegrationDemo()
            
        # Test with keys
        '
        os.environ['ARK_API_KEY']
        
        \
             patch('demo_vr, \
             patch('demo_volck_logger:
            
            mock_manager.retu
            
            mo()
        
        # Restore original environment
        if original_google_key:
ey
ron:
            del os.environ[Y']
            
        if original_ark_ke:
    
        ron:
            del os.environ['ARK_API_KEY']
        
        print("✅ Configu
        return True
        
    excepion as e:
        }")
        return Fa

def test_report_generation:
    """Test report generati"""
    print("🔍 Testing reportion...")
    
    try:
        fics
        
        , \
             patch \
             patch('demo_vo
            
            mock_manager.return_value.get_available_providers.ro"]
            
            demo = VolcanoIntegrationDemo()
            
            # Add some mock results
            demo.results = [
                DemoResult(
                    demo_name="Test Demo 1",
         e,
        cs=[
                        Pe),
                        PerformanceMetrics(provider="g
                    ]
                ),
            t(
                  ,
                    success=False,
            trics=[],
                  "
                )
            ]
            
            # Add ta
            demo.performance_data["volcano"] = [
                PerformanceMetrics(provider="volcano", rese=8.0),
            )
            ]
            demo.perfo] = [
                PerformanceMetrics(provider="google", response_time=5)
            ]
            
            # Test perfo
            performance_summary = demo._analyze_performance_dat)
            
            assert "volcano" in perforry
            assert "google" in performance_summary
            assert performanc.0
            1
            
            # Test recommendations
            s()
            assert isinstance( list)
            assert len(recommendations) > 0
           
            prin")
            return True
            
    except Exception as e:
        print(f"❌ Report generation test failed)
         False

def test_sample_ima):
    """T"
    print("🔍 Testing samp
    
    try:
        sample_images_dir = Pmages")
        readme_file 
    
t"
        assry"
        
        # Check README content
        with open(r:
    
            a
            assert "user_journey_flow.png" in content
            assert "conversion_funnel.png" in content
        
     t")
    True
        
    on as e:
        print(f"❌ Sample images t
        return False

def run_quick_demo_test():
    """Run a quick demo test with "
    print("🔍 Running quick demo test...")
    
    try:
        with patch('demo_volcanager, \
             patch('demo_volcano_integr
    r:
            
            # Configure mocks
    ()
            mock_llm.invoke.return_g"
            mock_llm.supports_m= True
            
            mock_manager.returllm
            mock_manager.retu
            
            mock_handler.retur]
            mock_handler.ret
            mock_handler.rext"
            
            from demo_volcano_
            
         )
            
            # Test ithods

mocks"
            
            text_res()
            assert text_resul)s else 10 if succesxit(    sys.en()
 mai =ssucce  s  _main__":
 == "_me___na

if _= 0d =eturn faile  r
    
  0)"*5t("=prin   )
    
 s above."ck the issuese cheed. Pleaailme tests fSot("⚠️      prin    else:
 
   ation.py")_integrmo_volcano  python de  print("      demo:")
  the full("\nTo runrint
        p") run. is ready tomo Des passed!🎉 All testnt("      pri0:
   == f failed   i 
 iled")
   d} fad, {faile passets: {passed}📊 Test Resulprint(f"")
    "\n{'='*50}nt(f   
    pri
 = 1ailed +  f          
 {e}")ashed:crname} (f"❌ {test_  print      
    n as e: Exceptio     except  d += 1
 faile                se:
  el       1
    +=  passed               t_func():
      if tes     
       try:
  me} ---") {test_na\n---int(f"     pr
   sts:n te test_func i_name,for test   
  0
      failed =0
  = ssed  pa   ]
    
 est)
   _demo_tquickst", run_o Tek Dem  ("Quic     s_setup),
 image_sample_st", testges TemaSample I     ("ion),
   _generateport", test_ration TestReport Gener        ("ck),
heon_curatinfig test_coheck Test",uration C"Config       (result),
  test_demo_",stsult TeRemo     ("Decs),
   metriance_rmest_perfo, tt"Metrics Tesrformance       ("Petion),
 lizainitiat_demo_es Test", tontitializa ("Ini,
       imports), test_demo_mport Test" ("I
         tests = [    
  "*50)
int("=pr")
    uiteemo Test Stion Draano Integ("🧪 Volc   print
 ests""" all t"Run ""):
   ef main(False

dreturn ()
        .print_excaceback        trraceback
  import t
      )e}" failed: {mo test❌ Quick det(f"    prin:
    as etion epExcexcept 
         rue
           return T      ed")
  t passck demo tes Quit("✅prin                      
"
  h mocksitceed wld sucalysis shou aness, "Textt.succ