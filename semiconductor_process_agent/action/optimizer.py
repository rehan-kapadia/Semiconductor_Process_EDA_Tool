from smt.surrogate_models import KRG
from scipy.optimize import minimize
import numpy as np

class ProcessOptimizer:
    """
    Uses a surrogate model to find optimal process parameters.
    """
    def __init__(self):
        print("ACTION [Optimizer]: Process Optimizer initialized.")

    def optimize(self, model_path: str, target_geometry: dict) -> dict:
        """
        Loads an SMT model and finds parameters to match target geometry.

        Args:
            model_path (str): Path to the saved SMT model file.
            target_geometry (dict): Dictionary of target outputs, e.g., {'thickness': 100.0}.

        Returns:
            dict: The optimized process parameters.
        """
        print(f"ACTION [Optimizer]: Optimizing for target {target_geometry} using model '{model_path}'")
        
        # In a real scenario, we would load the model:
        # smt_model = KRG.load(model_path)
        
        # For this example, we'll create a dummy model on the fly.
        # This model predicts 'thickness' based on 'time' and 'pressure'.
        xt = np.array([[10.0, 1.0], [20.0, 1.0], [10.0, 2.0], [20.0, 2.0]])
        yt = np.array([50.0, 100.0, 60.0, 120.0]) # Dummy thickness values
        smt_model = KRG(theta0=[1e-2, 1e-2])
        smt_model.set_training_values(xt, yt)
        smt_model.train()

        target_thickness = target_geometry['thickness']

        # Objective function for the optimizer
        def objective(params):
            # params[0] = time, params[1] = pressure
            predicted_thickness = smt_model.predict_values(np.array([params]))
            return (predicted_thickness[0][0] - target_thickness)**2

        # Initial guess and bounds for parameters
        initial_guess = [15.0, 1.5]
        bounds = [(5.0, 30.0), (0.5, 3.0)] # Time in seconds, Pressure in Torr

        result = minimize(objective, initial_guess, bounds=bounds, method='L-BFGS-B')

        if result.success:
            optimized_params = {
                'time_s': result.x[0],
                'pressure_torr': result.x[1],
                'achieved_thickness_nm': smt_model.predict_values(np.array([result.x]))[0][0]
            }
            print(f"ACTION [Optimizer]: Optimization successful. Params: {optimized_params}")
            return optimized_params
        else:
            print("ACTION [Optimizer]: Optimization failed.")
            return None
