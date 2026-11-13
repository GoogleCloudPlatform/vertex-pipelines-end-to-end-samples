from kfp.dsl import Artifact, Output, component


@component(
    base_image="python:3.12.8",
    packages_to_install=["google-cloud-aiplatform==1.135.0"],
)
def predict_on_endpoint(
    endpoint_id: str,
    project: str,
    predictions: Output[Artifact],
    location: str = "europe-west2",
    num_requests: int = 1500,
) -> None:
    """
    Send smoke-test prediction requests to a Vertex AI endpoint and save
    the results. Each request includes a small batch of varied instances;
    the request is repeated many times so model monitoring has enough
    logged traffic to produce plots. Which means you will see the same 10
    entries in the predictions output artifact.

    Args:
        endpoint_id: Vertex AI endpoint ID.
        project: GCP project ID.
        predictions: Output artifact where prediction results are saved.
        location: GCP region (default: europe-west2).
        num_requests: Number of prediction requests to send.
    """

    import json
    import logging

    import google.cloud.aiplatform as aip
    from google.api_core.exceptions import InternalServerError

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Varied smoke-test inputs (one request still uses this full batch).
    instances = [
        {
            "dayofweek": 4.0,
            "hourofday": 14.0,
            "trip_distance": 3210.5,
            "trip_miles": 2.1,
            "trip_seconds": 720.0,
            "payment_type": "Credit Card",
            "company": "Flash Cab",
        },
        {
            "dayofweek": 1.0,
            "hourofday": 8.0,
            "trip_distance": 1500.0,
            "trip_miles": 1.0,
            "trip_seconds": 360.0,
            "payment_type": "Cash",
            "company": "Taxi Affiliation Services",
        },
        {
            "dayofweek": 5.0,
            "hourofday": 18.0,
            "trip_distance": 8500.0,
            "trip_miles": 5.3,
            "trip_seconds": 1500.0,
            "payment_type": "Credit Card",
            "company": "Chicago Independents",
        },
        {
            "dayofweek": 6.0,
            "hourofday": 22.0,
            "trip_distance": 12000.0,
            "trip_miles": 7.5,
            "trip_seconds": 2100.0,
            "payment_type": "Credit Card",
            "company": "Flash Cab",
        },
        {
            "dayofweek": 2.0,
            "hourofday": 11.0,
            "trip_distance": 4800.0,
            "trip_miles": 3.0,
            "trip_seconds": 900.0,
            "payment_type": "Cash",
            "company": "Dispatch Taxi Affiliation",
        },
        {
            "dayofweek": 3.0,
            "hourofday": 7.0,
            "trip_distance": 2200.0,
            "trip_miles": 1.4,
            "trip_seconds": 480.0,
            "payment_type": "Credit Card",
            "company": "City Service",
        },
        {
            "dayofweek": 7.0,
            "hourofday": 16.0,
            "trip_distance": 15600.0,
            "trip_miles": 9.7,
            "trip_seconds": 2700.0,
            "payment_type": "Credit Card",
            "company": "Sun Taxi",
        },
        {
            "dayofweek": 4.0,
            "hourofday": 9.0,
            "trip_distance": 950.0,
            "trip_miles": 0.6,
            "trip_seconds": 180.0,
            "payment_type": "Cash",
            "company": "Flash Cab",
        },
        {
            "dayofweek": 5.0,
            "hourofday": 12.0,
            "trip_distance": 6400.0,
            "trip_miles": 4.0,
            "trip_seconds": 1200.0,
            "payment_type": "Credit Card",
            "company": "Taxi Affiliation Services",
        },
        {
            "dayofweek": 1.0,
            "hourofday": 20.0,
            "trip_distance": 24800.0,
            "trip_miles": 15.4,
            "trip_seconds": 3300.0,
            "payment_type": "Credit Card",
            "company": "Chicago Independents",
        },
    ]

    aip.init(project=project, location=location)

    endpoint = aip.Endpoint(
        endpoint_name=f"projects/{project}/locations/{location}/endpoints/{endpoint_id}",
    )

    # Repeat the same request many times so Vertex Model Monitoring gets enough
    # logged prediction traffic to produce drift/skew plots. This is intentional
    # volume generation, not an attempt to score many distinct rows.
    logger.info(
        "Sending %d request(s) (%d instance(s) each) to endpoint %s for smoke test and monitoring traffic",
        num_requests,
        len(instances),
        endpoint_id,
    )
    all_predictions = []
    max_retries = 3
    for i in range(num_requests):
        for attempt in range(max_retries):
            try:
                response = endpoint.predict(instances=instances)
                all_predictions.extend(response.predictions)
                if (i + 1) % 10 == 0 or i == 0:
                    logger.info("Request %d/%d succeeded", i + 1, num_requests)
                break
            except InternalServerError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(
                    "Prediction returned 500 (request %d, attempt %s/%s), retrying: %s",
                    i + 1, attempt + 1, max_retries, e,
                )

    result = {"predictions": all_predictions}
    with open(predictions.path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info("Saved %d prediction(s) from %d requests to %s", len(all_predictions), num_requests, predictions.path)
